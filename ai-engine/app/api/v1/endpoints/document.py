from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Request, Body
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
from app.core.config import settings

router = APIRouter()

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
VALID_MODES = {"syllabus", "pyq", "notes"}


@router.post("/document/process")
async def process_document(
    request: Request,
    file: UploadFile = File(...),
    mode: str = Query(...),
    flashcard_count: int = Query(10),
    notes_subtask: str = Query(""),
):
    if mode not in VALID_MODES:
        raise HTTPException(
            status_code=422,
            detail={"message": f"mode must be one of {sorted(VALID_MODES)}"},
        )
    if flashcard_count < settings.FLASHCARD_MIN or flashcard_count > settings.FLASHCARD_MAX:
        raise HTTPException(
            status_code=422,
            detail={"message": f"flashcard_count must be between {settings.FLASHCARD_MIN} and {settings.FLASHCARD_MAX}."},
        )
    if notes_subtask and notes_subtask not in ("flashcards", "exam", "summary"):
        raise HTTPException(
            status_code=422,
            detail={"message": "notes_subtask must be one of flashcards, exam, summary, or empty"},
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
    task_hint = TASK_MAP.get(mode.upper())
    chunks = chunk_text(text, task=task_hint)
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
    if notes_subtask:
        request.app.state.store.set_notes_subtask(job_id, notes_subtask)
    request.app.state.worker.submit(job_id)

    return JSONResponse(
        status_code=202,
        content={
            "job_id": job_id,
            "chunks_total": len(chunks),
            "mode_mismatch": mode_mismatch,
        },
    )


@router.post("/document/reprocess")
async def reprocess_chunks(
    request: Request,
    chunks: list[str] = Body(..., embed=True),
    mode: str = Query(...),
    flashcard_count: int = Query(10),
    notes_subtask: str = Query(""),
):
    if mode not in VALID_MODES:
        raise HTTPException(
            status_code=422,
            detail={"message": f"mode must be one of {sorted(VALID_MODES)}"},
        )
    if notes_subtask and notes_subtask not in ("flashcards", "exam", "summary"):
        raise HTTPException(
            status_code=422,
            detail={"message": "notes_subtask must be one of flashcards, exam, summary, or empty"},
        )
    if not chunks:
        raise HTTPException(
            status_code=422,
            detail={"message": "No chunks provided."},
        )
    if len(chunks) > 50:
        raise HTTPException(
            status_code=422,
            detail={"message": "Too many chunks. Maximum is 50."},
        )
    if any(len(c) > 50000 for c in chunks):
        raise HTTPException(
            status_code=422,
            detail={"message": "Chunk too large. Maximum is 50,000 characters per chunk."},
        )
    if flashcard_count < settings.FLASHCARD_MIN or flashcard_count > settings.FLASHCARD_MAX:
        raise HTTPException(
            status_code=422,
            detail={"message": f"flashcard_count must be between {settings.FLASHCARD_MIN} and {settings.FLASHCARD_MAX}."},
        )

    task = TASK_MAP[mode.upper()]
    job_id = str(uuid4())
    request.app.state.store.create_job(
        job_id,
        task=task,
        doc_type=mode.upper(),
        chunks=chunks,
        user_mode=mode,
        flashcard_count=flashcard_count,
    )

    # attach notes_subtask to the job record for worker routing
    if notes_subtask:
        request.app.state.store.set_notes_subtask(job_id, notes_subtask)

    request.app.state.worker.submit(job_id)

    return JSONResponse(
        status_code=202,
        content={
            "job_id": job_id,
            "chunks_total": len(chunks),
        },
    )
