from uuid import uuid4


def test_unknown_job_returns_404(make_client):
    client = make_client([])
    res = client.get(f"/api/v1/jobs/{uuid4()}")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"]["message"].lower()


def test_malformed_job_id_returns_422(make_client):
    client = make_client([])
    res = client.get("/api/v1/jobs/not-a-uuid")
    assert res.status_code == 422
    assert "invalid" in res.json()["detail"]["message"].lower()


def test_queued_job_has_no_payload_key(make_client):
    client = make_client([])
    store = client.app.state.store
    job_id = str(uuid4())
    store.create_job(job_id, task="notes", doc_type="NOTES", chunks=["a"])

    body = client.get(f"/api/v1/jobs/{job_id}").json()
    assert body["status"] == "queued"
    assert "payload" not in body
    assert "error" not in body


def test_failed_job_exposes_error(make_client):
    client = make_client([])
    store = client.app.state.store
    job_id = str(uuid4())
    store.create_job(job_id, task="notes", doc_type="NOTES", chunks=["a"])
    store.fail_job(job_id, "AI provider error (400): bad key")

    body = client.get(f"/api/v1/jobs/{job_id}").json()
    assert body["status"] == "failed"
    assert body["error"] == "AI provider error (400): bad key"
    assert "payload" not in body


def test_delete_cancels_active_job(make_client):
    client = make_client([])
    store = client.app.state.store
    job_id = str(uuid4())
    store.create_job(job_id, task="notes", doc_type="NOTES", chunks=["a"])

    res = client.delete(f"/api/v1/jobs/{job_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"
    assert store.get_job(job_id)["status"] == "cancelled"


def test_delete_is_idempotent_on_terminal_jobs(make_client):
    client = make_client([])
    store = client.app.state.store
    job_id = str(uuid4())
    store.create_job(job_id, task="notes", doc_type="NOTES", chunks=["a"])
    store.set_job_payload(job_id, '{"document_summary": "s"}')

    res = client.delete(f"/api/v1/jobs/{job_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "done"


def test_delete_unknown_job_returns_404(make_client):
    client = make_client([])
    res = client.delete(f"/api/v1/jobs/{uuid4()}")
    assert res.status_code == 404


def test_delete_malformed_id_returns_422(make_client):
    client = make_client([])
    res = client.delete("/api/v1/jobs/nope")
    assert res.status_code == 422
