from unittest.mock import MagicMock, patch

from app.parsers.pdf_extractor import EncryptedPDFError, InsufficientTextError
from tests.conftest import VALID_PAYLOADS

PDF_BYTES = b"%PDF-1.7\n" + b"x" * 100


def classification_mock(doc_type="NOTES", confidence=0.8):
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


def test_process_returns_202_with_job_id(make_client):
    client = make_client([VALID_PAYLOADS["NOTES"]])
    res = post_pdf(client, "NOTES")

    assert res.status_code == 202
    body = res.json()
    assert "job_id" in body
    assert body["chunks_total"] == 2
    job = client.app.state.store.get_job(body["job_id"])
    assert job["doc_type"] == "NOTES"
    assert job["task"] == "notes"


def test_process_end_to_end_reaches_done_with_payload(make_client):
    client = make_client([VALID_PAYLOADS["SYLLABUS"]])
    res = post_pdf(client, "SYLLABUS", mode="syllabus")
    job_id = res.json()["job_id"]

    client.app.state.worker.process_job_sync(job_id)

    status = client.get(f"/api/v1/jobs/{job_id}").json()
    assert status["status"] == "done"
    assert status["payload"]["course_title"] == "DS"


def test_llm_failure_surfaces_error_not_blank(make_client):
    from app.pipelines.llm_client import LLMError

    client = make_client([LLMError(400, "invalid api key", "groq", retryable=False)])
    res = post_pdf(client, "NOTES")
    job_id = res.json()["job_id"]

    client.app.state.worker.process_job_sync(job_id)

    status = client.get(f"/api/v1/jobs/{job_id}").json()
    assert status["status"] == "failed"
    assert "invalid api key" in status["error"]
    assert "payload" not in status


def test_encrypted_pdf_returns_400(make_client):
    client = make_client([])
    with patch("app.api.v1.endpoints.document.extract_text_from_pdf_bytes") as mock_extract:
        mock_extract.side_effect = EncryptedPDFError("PDF is encrypted")
        res = client.post(
            "/api/v1/document/process",
            files={"file": ("e.pdf", PDF_BYTES, "application/pdf")},
            params={"mode": "notes"},
        )
    assert res.status_code == 400
    assert "encrypted" in res.json()["detail"]["message"].lower()


def test_insufficient_text_returns_422(make_client):
    client = make_client([])
    with patch("app.api.v1.endpoints.document.extract_text_from_pdf_bytes") as mock_extract:
        mock_extract.side_effect = InsufficientTextError("Not enough text")
        res = client.post(
            "/api/v1/document/process",
            files={"file": ("empty.pdf", PDF_BYTES, "application/pdf")},
            params={"mode": "notes"},
        )
    assert res.status_code == 422
    assert "text" in res.json()["detail"]["message"].lower()


def test_no_file_returns_422(make_client):
    client = make_client([])
    res = client.post("/api/v1/document/process")
    assert res.status_code == 422


def test_non_pdf_returns_415(make_client):
    client = make_client([])
    res = client.post(
        "/api/v1/document/process",
        files={"file": ("readme.txt", b"hello world", "text/plain")},
        params={"mode": "notes"},
    )
    assert res.status_code == 415


def test_corrupt_pdf_bytes_return_400_not_500(make_client):
    client = make_client([])
    garbage = b"%PDF-1.7\nthis is definitely not a real pdf body"
    res = client.post(
        "/api/v1/document/process",
        files={"file": ("broken.pdf", garbage, "application/pdf")},
        params={"mode": "notes"},
    )
    assert res.status_code == 400
    assert "corrupt" in res.json()["detail"]["message"].lower()
