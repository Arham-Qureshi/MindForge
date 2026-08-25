from fastapi import APIRouter, UploadFile, File, HTTPException

from app.parsers.pdf_extractor import (
    extract_text_from_pdf_bytes,
    EncryptedPDFError,
    InsufficientTextError,
)
from app.classifiers.heuristic_engine import classify_document
from app.pipelines.chunker import chunk_text
from app.pipelines.syllabus_pipeline import process_syllabus
from app.pipelines.pyq_pipeline import process_pyq
from app.pipelines.notes_pipeline import process_notes

router = APIRouter()

MAX_UPLOAD_BYTES = 15 * 1024 * 1024


@router.post("/document/process")
async def process_document(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=415,
            detail={"message": "Only PDF files are accepted."},
        )

    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail={"message": "File exceeds 15 MB limit."},
        )

    try:
        text = extract_text_from_pdf_bytes(raw)
    except EncryptedPDFError as e:
        raise HTTPException(status_code=400, detail={"message": str(e)})
    except InsufficientTextError as e:
        raise HTTPException(status_code=422, detail={"message": str(e)})

    classification = classify_document(text)
    chunks = chunk_text(text)

    pipeline_map = {
        "SYLLABUS": process_syllabus,
        "PYQ": process_pyq,
        "NOTES": process_notes,
    }
    payload = pipeline_map[classification.doc_type](chunks)

    return {
        "classification": classification.model_dump(),
        "payload": payload.model_dump(),
    }
