"""CityBike-Sim: FastAPI application entry point.

Phase 5: mounts the WebSocket router at ``/api/v1`` for the real-time
simulation broadcast (bootstrap protocol + EventBus tick stream).
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.api.v1.ws import ws_router
from app.config import AppConfig

app = FastAPI(
    title="CityBike-Sim API",
    description="Urban shared bike simulation and visualization backend",
    version="0.1.0",
)

config = AppConfig()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1")
