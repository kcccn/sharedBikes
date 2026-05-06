"""API v1 router — 8 endpoint stubs."""

from fastapi import APIRouter

from app.models.schemas import (
    CitySummary,
    EventSchema,
    FleetSnapshotResponse,
    SimulationStatusResponse,
    StationSummary,
)

router = APIRouter()

# ── City ──────────────────────────────────────────────


@router.get("/city", response_model=CitySummary)
async def get_city_summary() -> CitySummary:
    raise NotImplementedError("Phase 1")


@router.get("/city/stations", response_model=list[StationSummary])
async def list_stations() -> list[StationSummary]:
    raise NotImplementedError("Phase 1")


# ── Fleet ─────────────────────────────────────────────


@router.get("/fleet", response_model=FleetSnapshotResponse)
async def get_fleet_snapshot() -> FleetSnapshotResponse:
    raise NotImplementedError("Phase 1")


# ── Simulation ────────────────────────────────────────


@router.post("/simulation/start")
async def start_simulation() -> dict:
    return {"message": "not implemented"}


@router.post("/simulation/pause")
async def pause_simulation() -> dict:
    return {"message": "not implemented"}


@router.get("/simulation/status", response_model=SimulationStatusResponse)
async def get_simulation_status() -> SimulationStatusResponse:
    raise NotImplementedError("Phase 1")


# ── Dashboard ─────────────────────────────────────────


@router.get("/dashboard/heatmap")
async def get_heatmap() -> dict:
    return {"message": "not implemented"}


@router.get("/dashboard/flows")
async def get_od_flows() -> dict:
    return {"message": "not implemented"}
