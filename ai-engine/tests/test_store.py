import json

from app.jobs.store import Store


def make_store(tmp_path):
    return Store(str(tmp_path / "jobs.db"))


def test_create_and_get_job(tmp_path):
    store = make_store(tmp_path)
    job_id = "j-1"
    store.create_job(job_id, task="notes", doc_type="NOTES", chunks=["a", "b", "c"])
    job = store.get_job(job_id)
    assert job["status"] == "queued"
    assert job["task"] == "notes"
    assert job["doc_type"] == "NOTES"
    assert job["chunks_total"] == 3
    assert job["chunks_done"] == 0


def test_get_missing_job_returns_none(tmp_path):
    store = make_store(tmp_path)
    assert store.get_job("nope") is None


def test_pending_chunks_roundtrip(tmp_path):
    store = make_store(tmp_path)
    store.create_job("j", task="syllabus", doc_type="SYLLABUS", chunks=["x", "y"])
    pending = store.pending_chunks("j")
    assert [p["text"] for p in pending] == ["x", "y"]
    assert pending[0]["attempts"] == 0


def test_complete_chunk_updates_progress(tmp_path):
    store = make_store(tmp_path)
    store.create_job("j", task="pyq", doc_type="PYQ", chunks=["a", "b"])
    store.mark_processing("j")
    store.complete_chunk("j", 0, json.dumps({"ok": True}))
    job = store.get_job("j")
    assert job["status"] == "processing"
    assert job["chunks_done"] == 1
    assert store.pending_chunks("j")[0]["idx"] == 1


def test_fail_chunk_attempts_marks_dead_at_max(tmp_path):
    store = make_store(tmp_path)
    store.create_job("j", task="notes", doc_type="NOTES", chunks=["only"])
    for _ in range(Store.MAX_ATTEMPTS):
        store.fail_chunk_attempt("j", 0)
    assert store.pending_chunks("j") == []
    assert store.dead_chunks_count("j") == 1


def test_fail_chunk_before_max_stays_pending(tmp_path):
    store = make_store(tmp_path)
    store.create_job("j", task="notes", doc_type="NOTES", chunks=["only"])
    store.fail_chunk_attempt("j", 0)
    pending = store.pending_chunks("j")
    assert len(pending) == 1
    assert pending[0]["attempts"] == 1


def test_fail_job_sets_error_status(tmp_path):
    store = make_store(tmp_path)
    store.create_job("j", task="notes", doc_type="NOTES", chunks=["a"])
    store.fail_job("j", "rate limited")
    job = store.get_job("j")
    assert job["status"] == "failed"
    assert job["error"] == "rate limited"


def test_payload_sets_done_status(tmp_path):
    store = make_store(tmp_path)
    store.create_job("j", task="notes", doc_type="NOTES", chunks=["a"])
    store.set_job_payload("j", json.dumps({"document_summary": "s"}))
    job = store.get_job("j")
    assert job["status"] == "done"
    assert json.loads(job["payload"])["document_summary"] == "s"


def test_purge_expired_removes_old_jobs_only(tmp_path):
    store = make_store(tmp_path)
    store.create_job("old", task="notes", doc_type="NOTES", chunks=["a"], created_at=1000.0)
    store.create_job("new", task="notes", doc_type="NOTES", chunks=["b"], created_at=9999999999.0)
    store.purge_expired(ttl_hours=1, now=2000000000.0)
    assert store.get_job("old") is None
    assert store.get_job("new") is not None


def test_usage_counters_roundtrip(tmp_path):
    store = make_store(tmp_path)
    snap = store.snapshot("groq")
    assert snap["reqs"] == 0 and snap["tokens"] == 0
    snap["reqs"] += 1
    snap["tokens"] += 500
    snap["win_start"] = 123.0
    store.save_snapshot("groq", snap)
    again = store.snapshot("groq")
    assert again["reqs"] == 1
    assert again["tokens"] == 500
    assert again["win_start"] == 123.0


def test_penalty_roundtrip(tmp_path):
    store = make_store(tmp_path)
    assert store.get_penalty("groq") == 0.0
    store.set_penalty("groq", 555.0)
    assert store.get_penalty("groq") == 555.0


def test_cancel_job_sets_cancelled_status(tmp_path):
    store = make_store(tmp_path)
    store.create_job("j", task="notes", doc_type="NOTES", chunks=["a"])
    store.cancel_job("j")
    job = store.get_job("j")
    assert job["status"] == "cancelled"
    assert "cancelled" in job["error"].lower()


def test_cancel_is_noop_on_terminal_jobs(tmp_path):
    store = make_store(tmp_path)
    store.create_job("j", task="notes", doc_type="NOTES", chunks=["a"])
    store.set_job_payload("j", "{}")
    store.cancel_job("j")
    assert store.get_job("j")["status"] == "done"


def test_done_write_cannot_override_cancelled(tmp_path):
    store = make_store(tmp_path)
    store.create_job("j", task="notes", doc_type="NOTES", chunks=["a"])
    store.cancel_job("j")
    store.set_job_payload("j", '{"document_summary": "late"}')
    assert store.get_job("j")["status"] == "cancelled"


def test_fail_write_cannot_override_cancelled(tmp_path):
    store = make_store(tmp_path)
    store.create_job("j", task="notes", doc_type="NOTES", chunks=["a"])
    store.cancel_job("j")
    store.fail_job("j", "some error")
    assert store.get_job("j")["status"] == "cancelled"


def test_processing_cannot_override_cancelled(tmp_path):
    store = make_store(tmp_path)
    store.create_job("j", task="notes", doc_type="NOTES", chunks=["a"])
    store.cancel_job("j")
    store.mark_processing("j")
    assert store.get_job("j")["status"] == "cancelled"
