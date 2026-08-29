import asyncio
import json
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, request: Request):
    job = _load_job(job_id, request)
    body = {
        "status": job["status"],
        "doc_type": job["doc_type"],
        "chunks_done": job["chunks_done"],
        "chunks_total": job["chunks_total"],
    }
    if job.get("classification"):
        body["classification"] = json.loads(job["classification"])
    if job["status"] == "done" and job["payload"]:
        body["payload"] = json.loads(job["payload"])
        body["raw_chunks"] = request.app.state.store.raw_chunks(job_id)
    if job["status"] == "failed" and job["error"]:
        body["error"] = job["error"]
    return body


@router.get("/jobs/{job_id}/stream")
async def stream_job(job_id: str, request: Request):
    _load_job(job_id, request)

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            job = request.app.state.store.get_job(job_id)
            if not job:
                break
            data = {
                "status": job["status"],
                "chunks_done": job["chunks_done"],
                "chunks_total": job["chunks_total"],
            }
            if job.get("classification"):
                data["classification"] = json.loads(job["classification"])
            if job["status"] == "done" and job["payload"]:
                data["payload"] = json.loads(job["payload"])
                data["raw_chunks"] = request.app.state.store.raw_chunks(job_id)
            if job["status"] == "failed" and job["error"]:
                data["error"] = job["error"]
            yield f"data: {json.dumps(data)}\n\n"
            if job["status"] in ("done", "failed", "cancelled"):
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str, request: Request):
    _load_job(job_id, request)
    # idempotent: cancelling a terminal job just reports its current state
    request.app.state.store.cancel_job(job_id)
    current = request.app.state.store.get_job(job_id)
    return {"status": current["status"] if current else "unknown"}


def _load_job(job_id: str, request: Request) -> dict:
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={"message": "Invalid job id."})

    job = request.app.state.store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"message": "Job not found."})
    return job
