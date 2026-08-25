import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.app import create_app


@pytest.fixture()
def client():
    return TestClient(create_app())


MOCK_CLASSIFICATION = {
    "doc_type": "SYLLABUS",
    "confidence": 0.85,
    "metrics": {"syllabus": {"count": 12, "matched_markers": ["module", "unit"]}},
}


@patch("app.api.v1.endpoints.document.process_notes")
@patch("app.api.v1.endpoints.document.process_pyq")
@patch("app.api.v1.endpoints.document.process_syllabus")
@patch("app.api.v1.endpoints.document.chunk_text")
@patch("app.api.v1.endpoints.document.classify_document")
@patch("app.api.v1.endpoints.document.extract_text_from_pdf_bytes")
def test_process_syllabus_returns_200(
    mock_extract, mock_classify, mock_chunk, mock_syllabus, mock_pyq, mock_notes, client
):
    mock_extract.return_value = "Syllabus content with enough words to pass validation checks."
    mock_classify.return_value = MagicMock(
        doc_type="SYLLABUS",
        confidence=0.85,
        metrics={"syllabus": {"count": 12, "matched_markers": ["module"]}},
        model_dump=MagicMock(return_value=MOCK_CLASSIFICATION),
    )
    mock_chunk.return_value = ["chunk1"]
    mock_syllabus.return_value = MagicMock(
        model_dump=MagicMock(return_value={"course_title": "DS", "total_units": 5, "learning_path": [], "priority_topics": []})
    )

    pdf_bytes = b"%PDF-1.7\n" + b"x" * 100
    res = client.post(
        "/api/v1/document/process",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )

    assert res.status_code == 200
    data = res.json()
    assert "classification" in data
    assert "payload" in data
    assert data["classification"]["doc_type"] == "SYLLABUS"
    mock_syllabus.assert_called_once()
    mock_pyq.assert_not_called()
    mock_notes.assert_not_called()


@patch("app.api.v1.endpoints.document.process_notes")
@patch("app.api.v1.endpoints.document.process_pyq")
@patch("app.api.v1.endpoints.document.process_syllabus")
@patch("app.api.v1.endpoints.document.chunk_text")
@patch("app.api.v1.endpoints.document.classify_document")
@patch("app.api.v1.endpoints.document.extract_text_from_pdf_bytes")
def test_process_routes_to_pyq(
    mock_extract, mock_classify, mock_chunk, mock_syllabus, mock_pyq, mock_notes, client
):
    mock_extract.return_value = "PYQ questions content with enough words."
    mock_classify.return_value = MagicMock(
        doc_type="PYQ",
        confidence=0.9,
        metrics={"pyq": {"count": 8, "matched_markers": ["question"]}},
        model_dump=MagicMock(return_value={"doc_type": "PYQ", "confidence": 0.9, "metrics": {}}),
    )
    mock_chunk.return_value = ["chunk1"]
    mock_pyq.return_value = MagicMock(
        model_dump=MagicMock(return_value={"topic_frequency": [], "predicted_questions": []})
    )

    pdf_bytes = b"%PDF-1.7\n" + b"x" * 100
    res = client.post(
        "/api/v1/document/process",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )

    assert res.status_code == 200
    mock_pyq.assert_called_once()
    mock_syllabus.assert_not_called()
    mock_notes.assert_not_called()


@patch("app.api.v1.endpoints.document.process_notes")
@patch("app.api.v1.endpoints.document.process_pyq")
@patch("app.api.v1.endpoints.document.process_syllabus")
@patch("app.api.v1.endpoints.document.chunk_text")
@patch("app.api.v1.endpoints.document.classify_document")
@patch("app.api.v1.endpoints.document.extract_text_from_pdf_bytes")
def test_process_routes_to_notes(
    mock_extract, mock_classify, mock_chunk, mock_syllabus, mock_pyq, mock_notes, client
):
    mock_extract.return_value = "Lecture notes content with enough words."
    mock_classify.return_value = MagicMock(
        doc_type="NOTES",
        confidence=0.7,
        metrics={"notes": {"count": 5, "matched_markers": ["definition"]}},
        model_dump=MagicMock(return_value={"doc_type": "NOTES", "confidence": 0.7, "metrics": {}}),
    )
    mock_chunk.return_value = ["chunk1"]
    mock_notes.return_value = MagicMock(
        model_dump=MagicMock(return_value={"document_summary": "ok", "flashcards": [], "practice_exam": []})
    )

    pdf_bytes = b"%PDF-1.7\n" + b"x" * 100
    res = client.post(
        "/api/v1/document/process",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )

    assert res.status_code == 200
    mock_notes.assert_called_once()
    mock_syllabus.assert_not_called()
    mock_pyq.assert_not_called()


@patch("app.api.v1.endpoints.document.extract_text_from_pdf_bytes")
def test_encrypted_pdf_returns_400(mock_extract, client):
    from app.parsers.pdf_extractor import EncryptedPDFError

    mock_extract.side_effect = EncryptedPDFError("PDF is encrypted")
    pdf_bytes = b"%PDF-1.7\n" + b"x" * 100
    res = client.post(
        "/api/v1/document/process",
        files={"file": ("encrypted.pdf", pdf_bytes, "application/pdf")},
    )

    assert res.status_code == 400
    assert "encrypted" in res.json()["detail"]["message"].lower()


@patch("app.api.v1.endpoints.document.extract_text_from_pdf_bytes")
def test_insufficient_text_returns_422(mock_extract, client):
    from app.parsers.pdf_extractor import InsufficientTextError

    mock_extract.side_effect = InsufficientTextError("Not enough text")
    pdf_bytes = b"%PDF-1.7\n" + b"x" * 100
    res = client.post(
        "/api/v1/document/process",
        files={"file": ("empty.pdf", pdf_bytes, "application/pdf")},
    )

    assert res.status_code == 422
    assert "text" in res.json()["detail"]["message"].lower()


def test_no_file_returns_422(client):
    res = client.post("/api/v1/document/process")
    assert res.status_code == 422


def test_non_pdf_returns_415(client):
    res = client.post(
        "/api/v1/document/process",
        files={"file": ("readme.txt", b"hello world", "text/plain")},
    )
    assert res.status_code == 415
