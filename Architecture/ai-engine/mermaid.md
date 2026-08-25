# MindForge AI-Engine — Architecture Diagrams

> Every diagram below mirrors the **actual code** in `ai-engine/app/` (function names, ports,
> error codes). Read each caption for what to notice.
>
> **How to view:** VS Code → install "Markdown Preview Mermaid Support" → open preview
> (`Ctrl+Shift+V`). GitHub/GitLab render these natively.

---

## 1. Overall System — Three Services, One Request Path

```mermaid
flowchart LR
    subgraph browser["Browser :5173"]
        UI["React SPA<br/>Dropzone / ProcessingView / ViewSwitcher"]
        LS[("localStorage<br/>mf.active_job")]
    end

    subgraph gw["server-gateway :5000"]
        UR["uploadRateLimiter<br/>5 req / 5 min (POST only)"]
        DC["document.controller"]
        JC["job.controller<br/>uuid-v4 gate"]
    end

    subgraph eng["ai-engine :8000 (FastAPI)"]
        EP["POST /api/v1/document/process<br/>202 {job_id}"]
        JP["GET·DELETE /api/v1/jobs/{id}"]
        WK["Worker thread + repair loop"]
        DB[("SQLite WAL<br/>jobs · job_chunks · usage")]
    end

    GROQ["Groq API<br/>gpt-oss-120b<br/>30 RPM / 8K TPM"]
    GEM["Gemini API<br/>2.5-flash<br/>10 RPM"]

    UI -->|"multipart PDF"| UR --> DC -->|"forward buffer"| EP
    UI -->|"poll every 2s"| JC --> JP
    UI <-.->|"job_id resume/kill"| LS
    EP --> WK <--> DB
    JP <--> DB
    WK -->|"syllabus + notes"| GROQ
    WK -->|"pyq only"| GEM
```

**What to notice:** the gateway never touches PDF bytes beyond a 4-byte `%PDF` sniff, and the
*upload* rate limit does not apply to job polling — otherwise 2-second polls would trip it instantly.

---

## 2. Upload Lifecycle — Every HTTP Hop

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant C as React (useJobSession)
    participant G as Gateway :5000
    participant E as Engine :8000
    participant W as Worker thread
    participant L as Groq/Gemini

    U->>C: drop PDF
    C->>G: POST /api/document/process (multipart)
    G->>E: POST /api/v1/document/process
    E->>E: validate → extract → classify → chunk
    E->>E: Store.create_job(job_id, chunks…)
    E-->>G: 202 {job_id, chunks_total}
    G-->>C: 202 (status passed through verbatim)
    C->>C: localStorage.setItem(mf.active_job)

    loop every 2000ms until terminal
        C->>G: GET /api/jobs/:id
        G->>E: GET /api/v1/jobs/:id
        E-->>C: {status, chunks_done, chunks_total}
    end

    par chunk fan-out (pool of 2)
        W->>L: chat.completions (JSON mode)
        L-->>W: JSON + usage tokens
    end

    E->>E: merge results → Store.set_job_payload (done)
    C->>G: GET /api/jobs/:id
    G-->>C: 200 {status:"done", payload, classification}
    C->>C: clear storage → ViewSwitcher renders
```

**What to notice:** the heavy LLM work happens *after* the 202. The client is never blocked;
progress (`chunks_done`) comes from the database, not from guessed timers like the old fake stages.

---

## 3. Engine Folder Map — Who Calls Whom

```mermaid
flowchart TD
    subgraph entry["app/ entry"]
        MAIN["__main__.py<br/>uvicorn :8000"] --> APPPY["app.py<br/>create_app() lifespan"]
    end

    APPPY -->|"builds"| STORE["jobs/store.py<br/>Store (SQLite)"]
    APPPY -->|"builds"| RL["pipelines/rate_limiter.py<br/>RateLimiter(store)"]
    APPPY -->|"builds"| WORKER["jobs/worker.py<br/>Worker(store, limiter)"]
    APPPY --> ROUTER["api/v1/router.py"]

    ROUTER --> HEALTH["endpoints/health.py"]
    ROUTER --> DOC["endpoints/document.py"]
    ROUTER --> JOBS["endpoints/jobs.py"]

    DOC --> PARSE["parsers/pdf_extractor.py<br/>PyMuPDF"]
    DOC --> CLS["classifiers/heuristic_engine.py"]
    DOC --> CHUNK["pipelines/chunker.py"]
    DOC -->|"create_job + submit"| STORE
    DOC -->|"submit(job_id)"| WORKER

    JOBS --> STORE

    WORKER -->|"pending/chunk writes"| STORE
    WORKER -->|"acquire/record"| RL
    WORKER -->|"complete()"| LLMC["pipelines/llm_client.py"]
    WORKER -->|"merge_*_results"| PIPES["pipelines/*_pipeline.py"]

    CHUNK --> TOKENS["pipelines/tokens.py<br/>tiktoken o200k"]
    LLMC --> CFG["core/config.py<br/>.env keys"]
    LLMC --> PROMPTS["prompts/__init__.py<br/>guards + skeletons"]
    PIPES --> SCHEMAS["schemas/*.py<br/>Pydantic contracts"]

    style STORE fill:#e1edff
    style RL fill:#fff3cd
    style WORKER fill:#ffe0e0
```

**What to notice:** `store`, `rate_limiter`, `worker` form the async triangle built once at app
startup. Endpoints are thin — they translate HTTP into calls on those three plus the pure
parse/classify/chunk functions. Nothing talks to an LLM except `llm_client`.

---

## 4. Inside POST /document/process — The Synchronous Half

```mermaid
sequenceDiagram
    autonumber
    participant R as Request (multipart)
    participant D as endpoints/document.py
    participant P as parsers/pdf_extractor
    participant H as classifiers/heuristic_engine
    participant K as pipelines/chunker
    participant S as jobs/store.py
    participant W as Worker

    R->>D: file bytes
    D->>D: content_type == application/pdf? else 415
    D->>D: len(raw) <= 15MB? else 413
    D->>P: extract_text_from_pdf_bytes(raw)
    alt fitz can't open
        P-->>D: CorruptPDFError → 400 (+log bytes/head)
    else password protected
        P-->>D: EncryptedPDFError → 400
    else < 50 words extracted
        P-->>D: InsufficientTextError → 422
    else text ok (first 100 pages)
        P-->>D: text
    end
    D->>H: classify_document(text[:5000])
    H-->>D: SYLLABUS | PYQ | NOTES (+confidence)
    D->>K: chunk_text(text)
    Note over K: heading split → token budget split<br/>(every chunk ≤ 2000 tok, guaranteed)
    D->>S: create_job(uuid4, TASK_MAP[type], chunks, classification)
    D->>W: submit(job_id)
    D-->>R: 202 {job_id, chunks_total}
```

**What to notice:** this half is *pure local work* — no network beyond the client. That's why the
gateway can afford a 30s timeout again. Every failure here is a specific HTTP code, never a 500.

---

## 5. Worker Repair Loop — Where Reliability Lives

```mermaid
flowchart TD
    Q["queue.get(job_id)"] --> GUARD["job exists? terminal? (_process_safely)"]
    GUARD -- "done / failed / cancelled" --> X1["return (nothing to do)"]
    GUARD -- "queued" --> MP["mark_processing<br/>(only if still queued)"]
    MP --> LOOP{"deadline exceeded?<br/>(15 min)"}

    LOOP -- yes --> FJ["fail_job('took too long')"]
    LOOP -- no --> CANCEL{"status == cancelled?"}
    CANCEL -- yes --> X2["return — user killed it"]
    CANCEL -- no --> TAKE["pending_chunks(attempts < 5)"]
    TAKE -- "empty" --> DONECHK{"any dead chunks?"}
    DONECHK -- yes --> FAILDEAD["fail_job('N chunks failed permanently')"]
    DONECHK -- no --> MERGE["merge_*_results(chunk_results)<br/>→ Pydantic payload"]
    MERGE --> SETP["set_job_payload → done"]

    TAKE -- "batch = first 2" --> POOL["ThreadPoolExecutor(2)"]
    POOL --> PC["_process_chunk × n"]
    PC --> AFTER{"status failed or<br/>cancelled after batch?"}
    AFTER -- yes --> X3["return"]
    AFTER -- no --> PROG{"progress this batch?"}
    PROG -- no --> BACK["sleep 2s (no-progress backoff)"]
    PROG -- yes --> LOOP
    BACK --> LOOP

    subgraph _process_chunk
        direction TB
        EST["estimate_request_tokens"] --> ACQ["RateLimiter.acquire"]
        ACQ -- DailyQuotaExhausted --> QFAIL["fail_job('daily quota exhausted')"]
        ACQ -- ok --> CALL["llm.complete(JSON mode)"]
        CALL -- "LLMError retryable" --> PEN["set_penalty(retry_after)"]
        PEN --> ATT["fail_chunk_attempt (+1)"]
        CALL -- "LLMError fatal" --> FATAL["fail_job(upstream message)"]
        CALL -- "json/schema/network error" --> ATT2["fail_chunk_attempt (+1)"]
        CALL -- valid JSON --> VAL["schema.model_validate"]
        VAL --> RC["limiter.record_usage(actual)"]
        RC --> CC["complete_chunk → done"]
    end
```

**What to notice:** three exits per chunk — succeed, retry-with-penalty, or die-after-5-attempts.
A dead chunk poisons the whole job *loudly* at the end. Silent blanks are structurally impossible:
`done` requires literally every chunk stored green.

---

## 6. Rate Limiter Decision Flow — The Toll Booth

```mermaid
flowchart TD
    IN["acquire(provider, est_tokens)"] --> BIG{"est_tokens >= TPM?"}
    BIG -- yes --> ERRV["ValueError — caller bug,<br/>impossible by construction"]
    BIG -- no --> PEN{"penalty_until > now?<br/>(retry-after from 429)"}
    PEN -- yes --> SLEEP1["sleep(penalty − now)"]
    SLEEP1 --> CHK
    PEN -- no --> CHK{"roll windows:<br/>new minute? new UTC day?"}

    CHK --> DAYQ{"day_reqs+1 > RPD<br/>or day_tokens+est > TPD?"}
    DAYQ -- yes --> DQX["raise DailyQuotaExhausted<br/>(reset_at midnight UTC)"]
    DAYQ -- no --> MINQ{"reqs+1 > RPM<br/>or tokens+est > TPM?"}
    MINQ -- yes --> WAIT["sleep(until window reset)"]
    WAIT --> CHK
    MINQ -- no --> RESERVE["reserve: reqs+=1, tokens+=est<br/>persist snapshot"]
    RESERVE --> SEND["HTTP send happens"]
    SEND --> REC["record_usage(actual_tokens):<br/>tokens += actual − est"]
```

**What to notice:** counters live in SQLite (`usage` table) — restart the engine mid-day and your
remaining daily quota is still honest. Reservation/reconciliation means bursts don't under-count
or over-count: we reserve the estimate, then true-up with `response.usage`.

---

## 7. Job State Machine

```mermaid
stateDiagram-v2
    [*] --> queued : POST /process (create_job)

    queued --> processing : worker picks up<br/>mark_processing (guarded: only from queued)
    processing --> processing : batches progress<br/>chunks_done++
    queued --> cancelled : DELETE /jobs/:id
    processing --> cancelled : DELETE /jobs/:id

    processing --> done : ALL chunks done<br/>merge → set_job_payload
    processing --> failed : fatal provider error
    processing --> failed : daily quota exhausted
    processing --> failed : any dead chunk (≥5 attempts)
    processing --> failed : 15-min deadline
    processing --> failed : internal crash (_process_safely guard)

    done --> [*]
    failed --> [*]
    cancelled --> [*]

    note right of cancelled
        Terminal states are write-guarded:
        done/fail updates carry
        WHERE status != 'cancelled'
        so stragglers can't resurrect a kill.
    end note
```

**What to notice:** cancellation is a *first-class terminal state*, not a flavour of failure. The
client treats `failed` and `cancelled` differently — one shows the engine's error, the other just
returns you to the uploader.

---

## 8. Kill Button — Cancellation Across Three Layers

```mermaid
sequenceDiagram
    autonumber
    participant U as User (ProcessingView)
    participant C as React (useJobSession.kill)
    participant G as Gateway DELETE /api/jobs/:id
    participant E as Engine DELETE /api/v1/jobs/:id
    participant S as Store (SQLite)
    participant W as Worker (mid-loop)

    U->>C: click Stop Processing
    C->>C: localStorage.clear + setActiveJob(null)<br/>→ UI back to Dropzone INSTANTLY
    C->>G: DELETE /api/jobs/:id (best-effort)
    G->>G: uuid-v4 regex? else 422 locally
    G->>E: DELETE /api/v1/jobs/:id
    E->>S: cancel_job WHERE status IN (queued,processing)
    S-->>E: rowcount (true = transitioned)
    E-->>C: 200 {status:"cancelled"}

    Note over W: next loop iteration reads status<br/>→ returns without writing anything
    Note over S: even an in-flight result write<br/>can't flip status (conditional UPDATEs)
```

**What to notice:** local-first ordering — the user sees instant feedback regardless of network.
Server-side cancellation is best-effort *for UX* but strict *for correctness*: idempotent DELETE,
guarded writes, worker abort between batches. An in-flight LLM call may finish, but its result
cannot resurrect the job.

---

## Cross-Cutting Invariants (memorise these)

1. **No chunk exceeds 2000 tokens** — force-split fallback closes every path.
2. **Every request fits inside one provider's TPM budget** — input estimate + output reserve.
3. **A job is `done` only when every chunk is `done`** — blanks are impossible by construction.
4. **Terminal states win** — all late writes are conditional on non-terminal status.
5. **Quota truth survives restarts** — counters are persisted, never in-memory-only.
