import json
import uuid

from fastapi import APIRouter, HTTPException, Request

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
    if job["status"] == "failed" and job["error"]:
        body["error"] = job["error"]
    return body


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
