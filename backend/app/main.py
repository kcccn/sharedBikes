"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.config import get_config

app = FastAPI(
    title="CityBike-Sim: Urban Operator",
    description="Real city bike-sharing simulation engine & API",
    version="0.1.0",
)

# ── Middleware ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────
app.include_router(v1_router, prefix="/api/v1")


@app.on_event("startup")
async def startup() -> None:
    _cfg = get_config()
    _cfg.data_dir.mkdir(parents=True, exist_ok=True)
    _cfg.osm_cache_dir.mkdir(parents=True, exist_ok=True)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
