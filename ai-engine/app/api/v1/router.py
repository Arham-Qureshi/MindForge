from fastapi import APIRouter

from app.api.v1.endpoints import health, document, jobs

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(document.router)
api_router.include_router(jobs.router)
