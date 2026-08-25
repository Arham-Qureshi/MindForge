import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router
from app.jobs.store import Store
from app.jobs.worker import Worker
from app.pipelines.rate_limiter import RateLimiter

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def create_app(store: Store | None = None, worker: Worker | None = None) -> FastAPI:
    if store is None:
        os.makedirs(_DATA_DIR, exist_ok=True)
        store = Store(os.path.join(_DATA_DIR, "jobs.db"))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        w: Worker | None = getattr(app.state, "worker", None)
        if w:
            w.start()
        yield
        if w:
            w.stop()

    app = FastAPI(title="MindForge AI Engine", version="0.2.0", lifespan=lifespan)

    app.state.store = store
    # tests inject a prebuilt worker (fake llm/limiter); production gets the real one
    app.state.worker = worker or Worker(store, limiter=RateLimiter(store))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    return app
