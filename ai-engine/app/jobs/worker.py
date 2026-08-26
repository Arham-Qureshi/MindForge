import json
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from app.jobs.store import Store
from app.pipelines.llm_client import llm_client as _default_llm, LLMError, PROVIDER_ROUTES, MAX_OUTPUT_TOKENS, DEFAULT_OUTPUT_RESERVE
from app.pipelines.rate_limiter import RateLimiter, DailyQuotaExhausted
from app.pipelines.syllabus_pipeline import merge_syllabus_results
from app.pipelines.pyq_pipeline import merge_pyq_results
from app.pipelines.notes_pipeline import merge_notes_results
from app.schemas.syllabus_schema import SyllabusPayload
from app.schemas.pyq_schema import PYQAnalysisPayload
from app.schemas.flashcard_schema import NotesPayload

TASK_MAP = {
    "SYLLABUS": "syllabus",
    "PYQ": "pyq",
    "NOTES": "notes",
}
MERGE_FNS = {
    "syllabus": merge_syllabus_results,
    "pyq": merge_pyq_results,
    "notes": merge_notes_results,
}
SCHEMAS = {
    "syllabus": SyllabusPayload,
    "pyq": PYQAnalysisPayload,
    "notes": NotesPayload,
}

POOL_SIZE = 2
JOB_DEADLINE_S = 15 * 60
NO_PROGRESS_BACKOFF_S = 2.0
JOB_TTL_HOURS = 6
PURGE_INTERVAL_S = 600


class Worker:
    """Single worker thread owns job state; LLM calls fan out on a small pool."""

    def __init__(self, store: Store, limiter: RateLimiter | None = None, llm=None,
                 deadline_seconds: float = JOB_DEADLINE_S):
        self.store = store
        self.limiter = limiter or RateLimiter(store)
        self.llm = llm or _default_llm
        self.deadline_seconds = deadline_seconds
        self._queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="mindforge-worker")
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._queue.put(None)
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def submit(self, job_id: str):
        self._queue.put(job_id)

    def _run(self):
        last_purge = 0.0
        while not self._stop_event.is_set():
            try:
                job_id = self._queue.get(timeout=1.0)
            except queue.Empty:
                now = time.time()
                if now - last_purge > PURGE_INTERVAL_S:
                    self.store.purge_expired(JOB_TTL_HOURS)
                    last_purge = now
                continue
            if job_id is None:
                break
            self._process_safely(job_id)

    # one guarded job execution, shared by the live loop and tests — an unexpected
    # crash must fail the job loudly, never kill the serving thread
    def _process_safely(self, job_id: str):
        try:
            self.process_job_sync(job_id)
        except Exception as e:
            self.store.fail_job(job_id, f"Internal processing error: {e}")

    def _run_once_for_test(self, job_id: str):
        self._process_safely(job_id)

    def process_job_sync(self, job_id: str):
        job = self.store.get_job(job_id)
        if not job or job["status"] in ("done", "failed", "cancelled"):
            return

        task = job.get("task") or TASK_MAP[job["doc_type"]]
        self.store.mark_processing(job_id)
        deadline = time.time() + self.deadline_seconds

        while True:
            current = self.store.get_job(job_id)
            if not current or current["status"] == "cancelled":
                return

            pending = self.store.pending_chunks(job_id)
            if not pending:
                break
            if time.time() > deadline:
                self.store.fail_job(job_id, "Processing took too long; please retry the upload.")
                return

            batch = pending[:POOL_SIZE]
            done_before = self.store.get_job(job_id)["chunks_done"]
            with ThreadPoolExecutor(max_workers=len(batch)) as pool:
                list(pool.map(lambda c: self._process_chunk(job_id, task, c, job), batch))

            # fatal/quota failures mark the job failed mid-flight; stop immediately
            status_after = self.store.get_job(job_id)["status"]
            if status_after in ("failed", "cancelled"):
                return

            done_after = self.store.get_job(job_id)["chunks_done"]

            if done_after == done_before and self.store.pending_chunks(job_id):
                # every call in this round failed transiently; ease off before retrying
                time.sleep(NO_PROGRESS_BACKOFF_S)

        dead = self.store.dead_chunks_count(job_id)
        if dead:
            self.store.fail_job(
                job_id,
                f"{dead} chunk(s) failed permanently after retries. Please try again.",
            )
            return

        results = self.store.chunk_results(job_id)
        payload = MERGE_FNS[task](results)
        self.store.set_job_payload(job_id, payload.model_dump_json())

    def _process_chunk(self, job_id: str, task: str, chunk: dict, job: dict | None = None):
        provider = PROVIDER_ROUTES.get(task, "groq")
        idx = chunk["idx"]
        chunk_text = chunk["text"]
        if task == "notes" and job:
            count = job.get("flashcard_count", 10)
            chunk_text = f"Generate exactly {count} flashcards.\n\n{chunk_text}"
        try:
            est = self.llm.estimate_request_tokens(task, chunk_text)
            self.limiter.acquire(provider, est)

            result = self.llm.complete(task=task, user=chunk_text, json_mode=True)
            data = json.loads(result.content)
            validated = SCHEMAS[task].model_validate(data).model_dump()

            self.limiter.record_usage(provider, result.total_tokens)
            self.store.complete_chunk(job_id, idx, json.dumps(validated))
        except DailyQuotaExhausted as e:
            self.store.fail_job(
                job_id,
                f"Daily free AI quota for {e.provider} is exhausted. Resets in a few hours.",
            )
        except LLMError as e:
            if e.retryable:
                if e.retry_after:
                    self.limiter.store.set_penalty(provider, time.time() + e.retry_after)
                self.store.fail_chunk_attempt(job_id, idx)
            else:
                # fatal upstream error (auth/config/oversize): retrying is pointless
                self.store.fail_job(job_id, f"AI provider error ({e.status}): {e.message}")
        except Exception:
            # network errors, invalid JSON, schema violations — worth a bounded retry
            self.store.fail_chunk_attempt(job_id, idx)
