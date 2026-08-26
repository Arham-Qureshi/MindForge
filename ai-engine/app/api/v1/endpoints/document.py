from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Request
from fastapi.responses import JSONResponse

from app.parsers.pdf_extractor import (
    extract_text_from_pdf_bytes,
    EncryptedPDFError,
    InsufficientTextError,
    CorruptPDFError,
)
from app.classifiers.heuristic_engine import classify_document
from app.pipelines.chunker import chunk_text
from app.jobs.worker import TASK_MAP

router = APIRouter()

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
VALID_MODES = {"syllabus", "pyq", "notes"}


@router.post("/document/process")
async def process_document(
    request: Request,
    file: UploadFile = File(...),
    mode: str = Query(...),
    flashcard_count: int = Query(10),
):
    if mode not in VALID_MODES:
        raise HTTPException(
            status_code=422,
            detail={"message": f"mode must be one of {sorted(VALID_MODES)}"},
        )

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
    except CorruptPDFError as e:
        raise HTTPException(status_code=400, detail={"message": str(e)})

    classification = classify_document(text)
    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(
            status_code=422,
            detail={"message": "Could not derive processable content from this PDF."},
        )

    doc_type = classification.doc_type
    mode_mismatch = doc_type.lower() != mode
    job_id = str(uuid4())
    request.app.state.store.create_job(
        job_id,
        task=TASK_MAP[mode.upper()],
        doc_type=doc_type,
        chunks=chunks,
        classification=classification.model_dump(),
        user_mode=mode,
        flashcard_count=flashcard_count,
    )
    request.app.state.worker.submit(job_id)

    return JSONResponse(
        status_code=202,
        content={
            "job_id": job_id,
            "chunks_total": len(chunks),
            "mode_mismatch": mode_mismatch,
        },
    )
