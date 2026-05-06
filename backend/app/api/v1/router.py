"""API v1 router: simulation, city, fleet, and dashboard endpoints."""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    BikeOut,
    CityOut,
    EventOut,
    FleetOut,
    FlowLine,
    HeatmapCell,
    SimConfigIn,
    SimStatusOut,
    StationOut,
)

api_router = APIRouter()


# ---- City ----

@api_router.get("/city", response_model=CityOut)
async def get_city():
    """Return city overview (stub)."""
    return CityOut(name="Beijing", station_count=0, zone_count=0)


@api_router.get("/city/stations", response_model=list[StationOut])
async def get_stations():
    """Return all stations (stub)."""
    return []


# ---- Fleet ----

@api_router.get("/fleet", response_model=FleetOut)
async def get_fleet():
    """Return current fleet state (stub)."""
    return FleetOut(total_bikes=0, active_rides=0, lost_bikes=0, bikes=[])


@api_router.get("/fleet/bikes/{bike_id}", response_model=BikeOut)
async def get_bike(bike_id: str):
    """Return a single bike (stub)."""
    raise HTTPException(status_code=404, detail="Bike not found")


# ---- Simulation ----

@api_router.post("/simulation/start", response_model=SimStatusOut)
async def start_simulation(config: SimConfigIn | None = None):
    """Start the simulation engine (stub)."""
    _ = config
    return SimStatusOut(tick=0, state="running", time_of_day="00:00")


@api_router.post("/simulation/pause", response_model=SimStatusOut)
async def pause_simulation():
    """Pause the simulation (stub)."""
    return SimStatusOut(tick=0, state="paused", time_of_day="00:00")


@api_router.post("/simulation/advance", response_model=SimStatusOut)
async def advance_simulation(steps: int = 1):
    """Advance simulation by N ticks (stub)."""
    _ = steps
    return SimStatusOut(tick=1, state="running", time_of_day="00:01")


@api_router.get("/simulation/status", response_model=SimStatusOut)
async def simulation_status():
    """Return current simulation status (stub)."""
    return SimStatusOut(tick=0, state="stopped", time_of_day="00:00")


# ---- Events ----

@api_router.get("/events", response_model=list[EventOut])
async def get_events():
    """Return active special events (stub)."""
    return []


# ---- Dashboard ----

@api_router.get("/dashboard/heatmap", response_model=list[HeatmapCell])
async def get_heatmap():
    """Return real-time demand heatmap cells (stub)."""
    return []


@api_router.get("/dashboard/flows", response_model=list[FlowLine])
async def get_flows():
    """Return OD flow lines for visualization (stub)."""
    return []
