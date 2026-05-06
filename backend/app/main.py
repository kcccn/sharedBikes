"""CityBike-Sim: FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.config import AppConfig
from app.core.city_config import CityConfig, CityConfigLoader, CityNotFoundError

app = FastAPI(
    title="CityBike-Sim API",
    description="Urban shared bike simulation and visualization backend",
    version="0.1.0",
)

config = AppConfig()
city_loader = CityConfigLoader()

# --- city config loaded at startup ---

try:
    _active_city: CityConfig = city_loader.load(config.city)
    print(f"[startup] Loaded city config: {_active_city.name} (ID: {config.city})")
except CityNotFoundError as exc:
    print(f"[startup] WARNING: {exc}")


def active_city() -> CityConfig:
    """Return the currently loaded active city config."""
    return _active_city


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/v1/cities", summary="List available city configs")
async def list_cities() -> list[str]:
    """Return IDs of all available city configurations."""
    return city_loader.list_cities()


@app.get("/api/v1/cities/active", summary="Get active city config")
async def get_active_city() -> CityConfig:
    """Return the currently active city configuration."""
    try:
        return active_city()
    except CityNotFoundError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=str(exc)) from exc


app.include_router(api_router, prefix="/api/v1")
