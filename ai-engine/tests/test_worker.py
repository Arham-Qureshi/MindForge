import json
import time

import pytest

from app.jobs.store import Store
from app.jobs.worker import Worker
from app.pipelines.llm_client import LLMError, LLMResult
from app.pipelines.rate_limiter import DailyQuotaExhausted

VALID_PAYLOADS = {
    "syllabus": {"course_title": "T", "total_units": 1, "learning_path": [], "priority_topics": []},
    "pyq": {"topic_frequency": [], "predicted_questions": []},
    "notes": {"document_summary": "s", "flashcards": [], "practice_exam": []},
}


class FakeLLM:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def estimate_request_tokens(self, task, user, flashcard_count=10):
        return 100

    def complete(self, task, user, model=None, json_mode=False, flashcard_count=10):
        self.calls.append(task)
        outcome = self.outcomes.pop(0) if len(self.outcomes) > 1 else self.outcomes[0]
        if isinstance(outcome, Exception):
            raise outcome
        return LLMResult(json.dumps(outcome), 120)


class FakeLimiterStore:
    def __init__(self):
        self.penalties = []

    def set_penalty(self, provider, until_ts):
        self.penalties.append((provider, until_ts))


class FakeLimiter:
    def __init__(self, acquire_error=None):
        self.store = FakeLimiterStore()
        self.acquire_error = acquire_error
        self.acquires = []
        self.recorded = []

    def acquire(self, provider, est_tokens):
        self.acquires.append((provider, est_tokens))
        if self.acquire_error:
            raise self.acquire_error

    def record_usage(self, provider, actual_tokens):
        self.recorded.append((provider, actual_tokens))


def make_worker(tmp_path, llm, limiter=None, deadline_seconds=300):
    store = Store(str(tmp_path / "jobs.db"))
    return (
        Worker(store, limiter=limiter or FakeLimiter(), llm=llm, deadline_seconds=deadline_seconds),
        store,
    )


def create_job(store, doc_type="NOTES", chunks=("c1", "c2")):
    task_map = {"SYLLABUS": "syllabus", "PYQ": "pyq", "NOTES": "notes_flashcards"}
    store.create_job("job-1", task=task_map[doc_type], doc_type=doc_type, chunks=list(chunks))
    return "job-1"


def test_all_chunks_success_merges_payload(tmp_path):
    llm = FakeLLM([VALID_PAYLOADS["notes"]])
    worker, store = make_worker(tmp_path, llm)
    job_id = create_job(store)

    worker.process_job_sync(job_id)

    job = store.get_job(job_id)
    assert job["status"] == "done"
    payload = json.loads(job["payload"])
    assert payload["document_summary"] == "s"


def test_fatal_error_fails_job_immediately(tmp_path):
    err = LLMError(400, "model not found", "groq", retryable=False)
    worker, store = make_worker(tmp_path, FakeLLM([err]))
    job_id = create_job(store)

    worker.process_job_sync(job_id)

    job = store.get_job(job_id)
    assert job["status"] == "failed"
    assert "model not found" in job["error"]


def test_retryable_error_then_success(tmp_path):
    err = LLMError(429, "rate limited", "groq", retryable=True, retry_after=2.0)
    llm = FakeLLM([err, VALID_PAYLOADS["notes"]])
    limiter = FakeLimiter()
    worker, store = make_worker(tmp_path, llm, limiter=limiter)
    job_id = create_job(store, chunks=("only",))

    worker.process_job_sync(job_id)

    assert store.get_job(job_id)["status"] == "done"
    assert limiter.recorded == [("groq", 120)]
    assert limiter.store.penalties and limiter.store.penalties[0][0] == "groq"


def test_persistent_transient_failures_exhaust_attempts(tmp_path):
    llm = FakeLLM([ValueError("bad json")])
    worker, store = make_worker(tmp_path, llm)
    job_id = create_job(store, chunks=("only",))

    worker.process_job_sync(job_id)

    job = store.get_job(job_id)
    assert job["status"] == "failed"
    assert "permanently" in job["error"]
    assert store.dead_chunks_count(job_id) == 1


def test_daily_quota_failure_fails_job_with_message(tmp_path):
    limiter = FakeLimiter(acquire_error=DailyQuotaExhausted("groq", reset_at=12345.0))
    worker, store = make_worker(tmp_path, FakeLLM([VALID_PAYLOADS["notes"]]), limiter=limiter)
    job_id = create_job(store)

    worker.process_job_sync(job_id)

    job = store.get_job(job_id)
    assert job["status"] == "failed"
    assert "quota" in job["error"].lower()


def test_deadline_exceeded_fails_job(tmp_path):
    worker, store = make_worker(
        tmp_path, FakeLLM([{"result": "x"}]), deadline_seconds=-1
    )
    job_id = create_job(store)

    worker.process_job_sync(job_id)

    job = store.get_job(job_id)
    assert job["status"] == "failed"
    assert "too long" in job["error"]


def test_thread_lifecycle_processes_submitted_job(tmp_path):
    llm = FakeLLM([VALID_PAYLOADS["notes"]])
    worker, store = make_worker(tmp_path, llm)
    job_id = create_job(store)

    worker.start()
    try:
        worker.submit(job_id)
        deadline = time.time() + 5
        while time.time() < deadline:
            if store.get_job(job_id)["status"] in ("done", "failed"):
                break
            time.sleep(0.02)
    finally:
        worker.stop()

    assert store.get_job(job_id)["status"] == "done"


def test_cancel_mid_processing_aborts_worker(tmp_path):
    llm = FakeLLM([VALID_PAYLOADS["notes"]])
    worker, store = make_worker(tmp_path, llm)
    job_id = create_job(store, chunks=("c1", "c2", "c3", "c4"))

    # simulate the user hitting DELETE while the loop is between batches
    original = worker.store.get_job

    def cancel_after_first_progress(job_id_arg):
        job = original(job_id_arg)
        if job["chunks_done"] >= 1 and job["status"] == "processing":
            store.cancel_job(job_id_arg)
        return job

    worker.store.get_job = cancel_after_first_progress
    worker.process_job_sync(job_id)

    assert store.get_job(job_id)["status"] == "cancelled"
    assert len(llm.calls) <= 4


def test_cancelled_queued_job_never_starts(tmp_path):
    llm = FakeLLM([VALID_PAYLOADS["notes"]])
    worker, store = make_worker(tmp_path, llm)
    job_id = create_job(store)
    store.cancel_job(job_id)

    worker.process_job_sync(job_id)

    assert store.get_job(job_id)["status"] == "cancelled"
    assert llm.calls == []


def test_unexpected_crash_fails_job_and_thread_serves_next(tmp_path):
    llm = FakeLLM([VALID_PAYLOADS["notes"], VALID_PAYLOADS["notes"]])
    worker, store = make_worker(tmp_path, llm)

    job_id = create_job(store)
    original_payload = store.set_job_payload

    def exploding_payload(jid, payload_json):
        raise RuntimeError("boom during merge write")

    store.set_job_payload = exploding_payload
    worker._run_once_for_test(job_id)

    job = store.get_job(job_id)
    assert job["status"] == "failed"
    assert "boom" in job["error"]

    # worker loop must still be functional: restore and process another job
    store.set_job_payload = original_payload
    other = "job-2"
    store.create_job(other, task="notes", doc_type="NOTES", chunks=["x"])
    worker._run_once_for_test(other)
    assert store.get_job(other)["status"] == "done"
