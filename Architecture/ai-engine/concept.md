# MindForge AI-Engine — Concepts & the Story of How It Got Here

> Written for one reader: **you, six months from now**, and for **you today** while the
> decisions are still fresh. Diagrams live next door in [`mermaid.md`](./mermaid.md) — this
> document explains *why* the shapes look that way.

---

## Part 0 — The One-Paragraph Version

MindForge turns an uploaded study PDF into structured assets (syllabus roadmaps, exam
predictions, flashcards + quizzes). Three local services cooperate: a React client (:5173), a
Node gateway (:5000) that owns security plumbing, and a Python FastAPI engine (:8000) that does
all intelligence. The engine never trusts the client, never touches disk for user files
(memory-only), and treats LLM providers what they actually are on free tiers: **shared,
metered infrastructure you must schedule around**, not infinite oracles.

---

## Part 1 — Why This Architecture Exists

### Local-first, zero-retention
Your PDFs are sensitive (entire semesters live in them). So: files exist only as in-memory
buffers (`multer.memoryStorage()` → `UploadFile.read()`), nothing is written to disk except
*operational metadata* (job rows), and payloads die when the job record is purged (6h TTL).
No cloud storage anywhere.

### Why three services instead of one?
- **Client** can't be trusted (browser = attacker-controlled) and can't hold secrets.
- **Gateway** exists to be the dumb, hardened bouncer: size limits, MIME sniffing, IP rate
  limits, CORS, uuid validation. It never inspects content.
- **Engine** holds API keys and does thinking. Only it talks to Groq/Gemini.
If the engine had the keys *and* faced the internet, every endpoint would be a security review.
Splitting means the attack surface facing users is deliberately boring.

### Why Python for the engine?
PyMuPDF (PDF parsing), fastembed (local embeddings), groq/google SDKs — the ML-adjacent ecosystem
lives in Python. Express would fight us; FastAPI gives async endpoints + Pydantic validation
for free.

---

## Part 2 — Folder Walkthrough (what each file is *for*)

Read top-down; each entry says the job **and why it's its own file**.

### `app.py` + `__main__.py` — composition root
Builds the FastAPI app, wires Store + RateLimiter + Worker once at startup (lifespan), mounts
routers under `/api/v1`, sets CORS. **Why separate:** dependency injection lives here — tests
swap in fakes via `create_app(store=..., worker=...)` without touching production wiring.

### `core/config.py` — the only place that reads `.env`
API keys, model names, allowed origins as typed Pydantic settings. **Why:** keys must exist in
exactly one object; anything else reading `os.environ` directly is a review flag.

### `api/v1/endpoints/` — HTTP translators (thin!)
| File | Job | Never does |
|---|---|---|
| `health.py` | liveness probe | anything |
| `document.py` | validate → extract → classify → chunk → create job → **202 {job_id}** | block on LLMs |
| `jobs.py` | read status / cancel (uuid-gated, idempotent DELETE) | business logic |

Endpoints translate HTTP ↔ domain calls. If an endpoint grows an `if` about chunking strategy,
that logic belongs lower.

### `parsers/pdf_extractor.py` — bytes → text, nothing else
PyMuPDF opens the stream; encrypted → `EncryptedPDFError`; <50 words → `InsufficientTextError`;
unopenable → `CorruptPDFError` (with a forensic log of byte length + first 8 bytes).
**Why exceptions, not HTTP codes:** this module doesn't know HTTP exists. The endpoint maps
domain errors to status codes (400/400/422). Layers stay honest.

### `classifiers/` — regex scoring, sub-millisecond routing
`regex_patterns.py` (marker lists per doc type) → `heuristic_engine.py` (count matches in first
5000 chars) → `score_calculator.py` (winner takes all; ties → NOTES; confidence = winner/total).
**Why heuristics instead of an LLM call:** classification happens *before* we know we can afford
any LLM calls at all. It must be free and instant.

### `pipelines/tokens.py` — ground truth for "how big is this?"
tiktoken `o200k_base` (gpt-oss tokenizer family) × 1.05 safety margin. `CHUNK_TOKEN_BUDGET =
2000`. **Why not estimate by words×1.33:** that estimator was how oversized requests slipped past
— words-to-tokens ratio drifts with language density. Measure like the provider measures.

### `pipelines/chunker.py` — budget-guaranteed splitting
Strategy: split on headings/double-newlines → any block over budget gets sentence-split → any
*sentence* over budget gets force-split into ~666-word windows (no embeddings — arbitrary word
groups carry no semantic signal anyway) → greedy packing under the budget → embedding-guided
boundaries (cosine-distance percentile) only for genuine sentence runs.
**Lesson baked in here:** the old version could emit one unbounded chunk from a punctuation-free
PDF. Every path now provably terminates under the cap — there's even a test asserting it for
pathological input.

### `pipelines/llm_client.py` — the only door to providers
- Routing: `PROVIDER_ROUTES = {"pyq": "gemini"}`, everything else Groq `openai/gpt-oss-120b`.
- Output reserves per task: syllabus 2500, notes/pyq 3000 tokens — chosen so
  **input + reserve always fits inside Groq's 8K TPM** (the bug that started everything).
- Returns `LLMResult(content, total_tokens)` so callers can reconcile limiter reservations.
- Raises `LLMError(status, message, provider, retryable, retry_after)` — a single taxonomy both
  backends map into. `json_validate_failed` (the model fumbling JSON) is retryable; bad keys and
  malformed requests are fatal.
- Prompt assembly (system template + task description + injection guard + XML-wrapped untrusted
  user text) also lives here, because prompt structure and provider quirks are inseparable.

### `prompts/__init__.py` — prompts are APIs
System prompt per task with a **literal JSON skeleton** declaring exact keys
(`practice_exam`, NOT `quiz_questions`), plus the defense-in-depth injection guard. The file's
header comment documents the whole security posture. **Lesson:** a schema validated *after*
generation is half a contract — the model must see the key names too, or it guesses
(and we watched it guess wrong).

### `schemas/*.py` — Pydantic contracts
Every field, enum and range (`weightage: float ge=0 le=1`). These are the *only* shapes that
reach the client. Model output that fails validation counts as a chunk failure and gets retried —
the client never sees raw model text.

### `pipelines/*_pipeline.py` — merge functions
Map-reduce without the ceremony: per-chunk results are merged with deduplication and
renormalisation (`merge_syllabus_results` dedupes units, renormalises weightages;
`merge_pyq_results` sums topic counts, keeps best-probability duplicate questions;
`merge_notes_results` keeps longest summary, dedupes cards).

### `pipelines/rate_limiter.py` — scheduling, not apologising
Sliding windows persisted in SQLite: RPM/RPD counters + token buckets per provider, penalty
timestamps honouring provider `retry-after` headers, `acquire()` blocks until permission,
`record_usage()` trues-up estimates against real usage. Daily exhaustion raises
`DailyQuotaExhausted(reset_at)` so jobs fail with *"resets in a few hours"* instead of hammering
a dead budget. **Mental model: a toll booth between your worker and the internet.**

### `jobs/store.py` — the database layer
Three tables:
- `jobs` — status machine rows (+ classification snapshot, merged payload)
- `job_chunks` — per-chunk text/status/attempts/result; doubles as the **repair queue**
- `usage` — provider quota counters + penalties

Everything thread-safe behind one RLock, WAL journal mode. Terminal writes are conditional
(`WHERE status != 'cancelled'`) so late results can't resurrect killed jobs.

### `jobs/worker.py` — the heartbeat
One worker thread owns the queue; a 2-thread pool overlaps network latency inside each batch of
2 chunks. Per chunk: estimate → acquire → complete → validate → store. Repair loop re-enqueues
failed chunks until attempts hit 5 (dead), the 15-minute deadline hits, or the user cancels —
cancellation is checked *between batches*. Any unexpected crash fails *that job* through the
`_process_safely` guard and the thread keeps serving. **Why a single worker:** SQLite writes have
one owner (no lock contention), and free-tier quotas couldn't feed more concurrency anyway.

---

## Part 3 — The Day Everything Broke (and what each break taught)

A true story in five acts, kept because the lessons are the real deliverable.

### Act I — The blank screen that lied
Upload a small PDF → UI shows success-shaped emptiness. No error anywhere.
**Forensics:** the Groq dashboard showed requests… all `413`.
**Lesson 1 — Silent failure handling produces confident lies.**
`except Exception: return {}` turned hard failures into empty-but-successful responses. Blank
output wasn't a rendering bug; it was an honesty bug. Now: failures are terminal states the UI
must display; blanks are structurally impossible (`done` requires every chunk green).

### Act II — 413 ≠ "file too large"
Groq's 413 meant *"this request alone exceeds your entire per-minute token budget."*
Our `max_tokens=8192` was bigger than the free tier's total 8K TPM — every request was rejected
at admission, regardless of payload size.
**Lesson 2 — Read provider limits as admission control, not throttling.**
TPM caps the *single request*, not just your average throughput. Fix: per-task output reserves
(2500–3000) sized so input + output < ceiling, always.

### Act III — The estimator that lied by 30%
`words × 1.33` under-counts dense text, and a PDF without sentence boundaries produced one giant
"sentence" no splitter could bound.
**Lesson 3 — Budget with the provider's own ruler.**
tiktoken o200k + 1.05 margin + a force-split fallback that closes *every* path, verified by a
test feeding pathological input.

### Act IV — Retries that made things worse
5 concurrent workers firing blind = quota burn with no coordination, retrying doomed payloads.
**Lesson 4 — Rate limiting is architecture, not error handling.**
Persisted sliding windows + pre-send reservation/reconciliation + `retry-after` penalties +
daily-quota circuit breaker. Threads give concurrency; the limiter gives permission.

### Act V — The model guessed our schema
Post-fix forensics (reading our own SQLite!) caught Groq emitting beautiful JSON with
`"quiz_questions"` and `"summary"` keys — names we never sent it.
**Lesson 5 — A schema validated after generation is half a contract.**
Prompts now carry literal JSON skeletons; validation failures became retryable
(`json_validate_failed`) instead of job-fatal, because a model fumbling formatting is transient
by nature.

---

## Part 4 — One Request's Complete Life (trace with me)

1. **Click.** `Dropzone.tsx` → `useFileUpload.upload()` validates type/size locally.
2. **POST** → gateway `upload.middleware.ts` buffers in RAM, `validatePDFHeader` sniffs `%PDF`,
   upload rate limiter counts the IP → `document.controller` forwards buffer verbatim.
3. **Engine admits** (`endpoints/document.py`): 415/413 checks → `pdf_extractor` (corrupt/
   encrypted/thin-text mapped to 400/400/422) → `classify_document` (first 5000 chars) →
   `chunk_text` (≤2000 tok guaranteed) → `Store.create_job(uuid4, task, chunks, classification)`
   → `Worker.submit(job_id)` → **202 `{job_id, chunks_total}`** back through gateway untouched.
4. **Client persists** `mf.active_job` to localStorage → renders `ProcessingView`
   (boxes = chunks_total, wave animation, k/n counter, Stop button).
5. **Worker loop**: marks processing → takes ≤2 pending chunks → pool threads race ahead but the
   **limiter gates actual sends** → Groq/Gemini JSON-mode calls → Pydantic validation →
   `complete_chunk` + usage true-up. Failures re-enqueue with penalties; 5 attempts → dead.
6. **Merge & finish**: all chunks done → `merge_*_results` → `set_job_payload` → status `done`.
7. **Poll pays off**: next 2-second tick sees `done`, composes
   `{classification, payload}` → `ViewSwitcher` routes SYLLABUS/PYQ/NOTES → flashcards render.
8. **Or the exits**: failed → error screen shows the *engine's actual message*; cancelled →
   quiet return to uploader; refresh mid-flight → localStorage resume jumps straight back to step 7's polling; engine restart mid-job → SQLite state survives, worker resumes serving.

---

## Part 5 — Glossary (the words that kept appearing)

| Term | Plain meaning |
|---|---|
| **RPM / RPD** | Requests per minute / day — *count* ceilings |
| **TPM / TPD** | Tokens (in+out) per minute / day — *size* ceilings; TPM also caps any single request |
| **Admission control** | Provider rejects before processing if a request *could* exceed budget |
| **Sliding/fixed window** | Counting technique; ours are fixed minute/day buckets, rolled lazily |
| **Reservation + reconciliation** | Pre-charge estimated tokens, refund/charge the delta after real usage |
| **Repair queue** | Failed units re-enqueue with attempt budgets instead of dying silently |
| **Terminal state** | done/failed/cancelled — guarded so late writes can't change them |
| **Idempotent DELETE** | Cancelling twice (or after completion) is safe and reports truth |
| **WAL mode** | SQLite journal allowing concurrent readers with one writer |
| **Backpressure** | Sleeping/pausing producers when downstream (quota) is saturated |
| **Prompt-schema contract** | Model must be told exact keys AND output must be validated — both halves |

---

## Part 6 — Honest Tradeoffs (what this design can't do yet)

- **Single worker thread** — jobs process one-at-a-time. Fine for you; wrong for multi-user.
- **No auth** — anyone who can reach :5000 uses your quota. Trust model = localhost.
- **Free-tier ceilings** — ~1000 Groq req/day ≈ a handful of large documents. Paid tier is a
  config change (limits table), which was the point of centralising the limiter.
- **SQLite** — perfect for one process; swap for Postgres only if jobs outlive one machine.
- **Chunk-level context loss** — each chunk sees itself, not the document. Merge functions
  paper over some of it; cross-chunk reasoning (e.g., unit numbering across pages) is best-effort.
- **fastembed at startup** — first heavy chunk triggers a model load (~seconds); acceptable
  locally, worth pre-warming if this ever serves real traffic.

Each tradeoff was chosen *on purpose* for a learner-local build. Knowing exactly where the walls
are is what makes the next refactor boring instead of brave.
