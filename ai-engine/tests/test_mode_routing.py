from unittest.mock import patch

from tests.conftest import VALID_PAYLOADS

PDF_BYTES = b"%PDF-1.7\n" + b"x" * 100


def classification_mock(doc_type="NOTES", confidence=0.8):
    from unittest.mock import MagicMock
    m = MagicMock(
        doc_type=doc_type,
        confidence=confidence,
        metrics={"x": {"count": 1, "matched_markers": []}},
    )
    m.model_dump.return_value = {
        "doc_type": doc_type,
        "confidence": confidence,
        "metrics": {},
    }
    return m


def post_pdf(client, doc_type="NOTES", mode="notes"):
    with (
        patch("app.api.v1.endpoints.document.extract_text_from_pdf_bytes") as mock_extract,
        patch("app.api.v1.endpoints.document.classify_document") as mock_classify,
        patch("app.api.v1.endpoints.document.chunk_text") as mock_chunk,
    ):
        mock_extract.return_value = "enough words " * 20
        mock_classify.return_value = classification_mock(doc_type)
        mock_chunk.return_value = ["chunk-one", "chunk-two"]
        return client.post(
            "/api/v1/document/process",
            files={"file": ("test.pdf", PDF_BYTES, "application/pdf")},
            params={"mode": mode},
        )


def test_mode_required(make_client):
    client = make_client([])
    with (
        patch("app.api.v1.endpoints.document.extract_text_from_pdf_bytes") as mock_extract,
        patch("app.api.v1.endpoints.document.classify_document") as mock_classify,
        patch("app.api.v1.endpoints.document.chunk_text") as mock_chunk,
    ):
        mock_extract.return_value = "enough words " * 20
        mock_classify.return_value = classification_mock("NOTES")
        mock_chunk.return_value = ["chunk-one"]
        res = client.post(
            "/api/v1/document/process",
            files={"file": ("test.pdf", PDF_BYTES, "application/pdf")},
        )
    assert res.status_code == 422


def test_mode_stored_in_job(make_client):
    client = make_client([VALID_PAYLOADS["NOTES"]])
    res = post_pdf(client, doc_type="NOTES", mode="notes")
    assert res.status_code == 202
    job = client.app.state.store.get_job(res.json()["job_id"])
    assert job["user_mode"] == "notes"


def test_mode_overrides_doc_type(make_client):
    client = make_client([VALID_PAYLOADS["SYLLABUS"]])
    res = post_pdf(client, doc_type="NOTES", mode="syllabus")
    assert res.status_code == 202
    job = client.app.state.store.get_job(res.json()["job_id"])
    assert job["task"] == "syllabus"


def test_mode_mismatch_flag(make_client):
    client = make_client([VALID_PAYLOADS["NOTES"]])
    res = post_pdf(client, doc_type="NOTES", mode="syllabus")
    assert res.status_code == 202
    body = res.json()
    assert body["mode_mismatch"] is True


def test_no_mismatch_when_aligned(make_client):
    client = make_client([VALID_PAYLOADS["NOTES"]])
    res = post_pdf(client, doc_type="NOTES", mode="notes")
    assert res.status_code == 202
    body = res.json()
    assert body["mode_mismatch"] is False


def test_worker_uses_user_mode_for_routing(make_client):
    """Worker should route based on user_mode, not doc_type."""
    client = make_client([VALID_PAYLOADS["NOTES"]])
    res = post_pdf(client, doc_type="SYLLABUS", mode="notes")
    job_id = res.json()["job_id"]
    client.app.state.worker.process_job_sync(job_id)
    status = client.get(f"/api/v1/jobs/{job_id}").json()
    assert status["status"] == "done"
    assert "document_summary" in status["payload"]


def test_flashcard_count_stored(make_client):
    client = make_client([VALID_PAYLOADS["NOTES"]])
    with (
        patch("app.api.v1.endpoints.document.extract_text_from_pdf_bytes") as mock_extract,
        patch("app.api.v1.endpoints.document.classify_document") as mock_classify,
        patch("app.api.v1.endpoints.document.chunk_text") as mock_chunk,
    ):
        mock_extract.return_value = "enough words " * 20
        mock_classify.return_value = classification_mock("NOTES")
        mock_chunk.return_value = ["chunk-one"]
        res = client.post(
            "/api/v1/document/process",
            files={"file": ("test.pdf", PDF_BYTES, "application/pdf")},
            params={"mode": "notes", "flashcard_count": 25},
        )
    assert res.status_code == 202
    job = client.app.state.store.get_job(res.json()["job_id"])
    assert job["flashcard_count"] == 25
