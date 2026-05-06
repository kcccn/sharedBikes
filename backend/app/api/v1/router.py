"""API v1 router — all simulation endpoints are defined here."""

from fastapi import APIRouter

api_router = APIRouter()


# ── City endpoints ────────────────────────────────────────────────

@api_router.get("/city")
async def get_city():
    """Return the current city / road-network metadata."""
    return {"message": "not implemented"}


@api_router.get("/city/stations")
async def list_stations():
    """List all stations (name, position, capacity, inventory)."""
    return {"message": "not implemented"}


# ── Fleet endpoints ───────────────────────────────────────────────

@api_router.get("/fleet")
async def get_fleet_snapshot():
    """Return a snapshot of all bikes and their current state."""
    return {"message": "not implemented"}

@api_router.post("/fleet/dock")
async def dock_bike():
    """Manually dock a bike at a station."""
    return {"message": "not implemented"}

@api_router.post("/fleet/undock")
async def undock_bike():
    """Manually undock a bike from a station."""
    return {"message": "not implemented"}


# ── Simulation control endpoints ──────────────────────────────────

@api_router.post("/simulation/start")
async def start_simulation():
    """Start (or resume) the simulation engine."""
    return {"message": "not implemented"}

@api_router.post("/simulation/pause")
async def pause_simulation():
    """Pause the simulation engine."""
    return {"message": "not implemented"}


# ── Dashboard / analytics endpoints ───────────────────────────────

@api_router.get("/dashboard/heatmap")
async def heatmap_data():
    """Return supply-demand heatmap data for the current tick."""
    return {"message": "not implemented"}

@api_router.get("/dashboard/flows")
async def od_flow_data():
    """Return origin-destination flow data for visualisation."""
    return {"message": "not implemented"}
