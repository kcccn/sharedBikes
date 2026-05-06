"""v1 API router — map endpoints to service handlers."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/city")
async def get_city_info():
    """Return loaded city metadata & road network stats."""
    return {"message": "not implemented"}


@router.get("/fleet")
async def get_fleet_status():
    """Return current fleet state (bikes per station, utilization)."""
    return {"message": "not implemented"}


@router.get("/simulation/state")
async def get_simulation_state():
    """Return current simulation tick, time-of-day, speed."""
    return {"message": "not implemented"}


@router.post("/simulation/start")
async def start_simulation():
    """Start / resume the simulation loop."""
    return {"message": "not implemented"}


@router.post("/simulation/pause")
async def pause_simulation():
    """Pause the simulation loop."""
    return {"message": "not implemented"}


@router.get("/dashboard/heatmap")
async def get_heatmap():
    """Return supply/demand heatmap data for frontend rendering."""
    return {"message": "not implemented"}


@router.get("/dashboard/flows")
async def get_od_flows():
    """Return origin-destination flow lines for frontend animation."""
    return {"message": "not implemented"}
