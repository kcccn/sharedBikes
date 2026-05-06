"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.config import AppConfig

config = AppConfig()

app = FastAPI(
    title="CityBike-Sim API",
    description="Urban bike-sharing simulation engine",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
