"""CityBike-Sim: FastAPI application entry point."""

from fastapi import FastAPI

from app.api.v1.router import api_router
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
