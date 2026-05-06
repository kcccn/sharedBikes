"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.v1.router import router as api_router
from app.config import config

app = FastAPI(
    title=config.app_name,
    version="0.1.0",
    docs_url="/docs",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok", "app": config.app_name}
