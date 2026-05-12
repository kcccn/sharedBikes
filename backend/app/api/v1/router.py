"""API v1 router: simulation, city, fleet, and dashboard endpoints.

Phase 4 wiring: all simulation/*, /fleet, and /events endpoints now read
from the live SimulationEngine via the EngineManager singleton.
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    BikeOut,
    CityOut,
    EdgeOut,
    EventOut,
    FleetOut,
    FlowLine,
    HeatmapCell,
    LeaderboardEntryOut,
    NodeOut,
    SimConfigIn,
    SimStatusOut,
    StationOut,
    StationStatsOut,
    ZoneOut,
)
from app.services.engine_manager import EngineManager
from app.services.map_service import MapService

api_router = APIRouter()
_map_service = MapService()
_engine_mgr = EngineManager()  # singleton


def _get_city_data(city_name: str = "default") -> CityOut:
    """Build a CityOut response from the MapService."""
    city = _map_service.load_city(city_name)
    nodes_out = [
        NodeOut(
            node_id=n.node_id,
            x=n.position.x,
            y=n.position.y,
            elevation_m=n.elevation_m,
        )
        for n in city.nodes.values()
    ]
    edges_out = [
        EdgeOut(
            edge_id=e.edge_id,
            from_node=e.from_node,
            to_node=e.to_node,
            length_m=e.length_m,
            max_speed_kmh=e.max_speed_kmh,
        )
        for e in city.edges.values()
    ]
    stations_out = [
        StationOut(
            station_id=s.station_id,
            x=s.position.x,
            y=s.position.y,
            capacity=s.capacity,
            name=s.name,
        )
        for s in city.stations.values()
    ]
    zones_out = [
        ZoneOut(
            zone_id=z.zone_id,
            name=z.name,
            polygon=[(p.x, p.y) for p in z.polygon],
        )
        for z in city.zones.values()
    ]
    return CityOut(
        name=city_name,
        node_count=len(city.nodes),
        edge_count=len(city.edges),
        station_count=len(city.stations),
        zone_count=len(city.zones),
        nodes=nodes_out,
        edges=edges_out,
        stations=stations_out,
        zones=zones_out,
    )


# ---- City ----

@api_router.get("/city", response_model=CityOut)
async def get_city():
    """Return full city data (nodes, edges, stations, zones)."""
    return _get_city_data()


@api_router.get("/city/stations", response_model=list[StationOut])
async def get_stations():
    """Return all stations."""
    city = _map_service.load_city("default")
    return [
        StationOut(
            station_id=s.station_id,
            x=s.position.x,
            y=s.position.y,
            capacity=s.capacity,
            name=s.name,
        )
        for s in city.stations.values()
    ]


# ---- Fleet ----

@api_router.get("/fleet", response_model=FleetOut)
async def get_fleet():
    """Return current fleet state from the live engine."""
    return _engine_mgr.get_fleet()


@api_router.get("/fleet/bikes/{bike_id}", response_model=BikeOut)
async def get_bike(bike_id: str):
    """Return a single bike from the live engine."""
    bike = _engine_mgr.get_bike(bike_id)
    if bike is None:
        raise HTTPException(status_code=404, detail="Bike not found")
    return bike


# ---- Simulation ----

@api_router.post("/simulation/start", response_model=SimStatusOut)
async def start_simulation(config: SimConfigIn | None = None):
    """Start the simulation engine.

    Accepts an optional ``SimConfigIn`` to override default parameters.
    Idempotent — safe to call on an already-running engine.
    """
    _ = config  # TODO: apply config overrides after engine restart
    return _engine_mgr.start()


@api_router.post("/simulation/pause", response_model=SimStatusOut)
async def pause_simulation():
    """Pause the simulation engine."""
    return _engine_mgr.pause()


@api_router.post("/simulation/advance", response_model=SimStatusOut)
async def advance_simulation(steps: int = 1):
    """Advance the simulation by *steps* ticks."""
    return _engine_mgr.advance(steps)


@api_router.get("/simulation/status", response_model=SimStatusOut)
async def simulation_status():
    """Return current simulation status from the live engine."""
    return _engine_mgr.get_status()


# ---- Events ----

@api_router.get("/events", response_model=list[EventOut])
async def get_events():
    """Return active special events from the engine's environment."""
    return _engine_mgr.get_events()


# ---- Dashboard ----

@api_router.get("/dashboard/heatmap", response_model=list[HeatmapCell])
async def get_heatmap():
    """Return real-time demand heatmap cells from StationStatsTracker.

    Phase 6 P2: Replaces the Phase 5 stub with real demand_factor data.
    Each cell represents a station with its demand intensity [0.0, 1.0]
    normalized by max ``trips_completed`` across all stations.
    """
    tracker = _engine_mgr.station_stats_tracker
    city = _map_service.load_city("default")
    factors = tracker.get_demand_factors()
    cells: list[HeatmapCell] = []
    for sid_str, intensity in factors.items():
        station = city.stations.get(sid_str)
        if station is not None:
            cells.append(HeatmapCell(
                x=station.position.x,
                y=station.position.y,
                intensity=intensity,
            ))
    return cells


@api_router.get("/dashboard/flows", response_model=list[FlowLine])
async def get_flows():
    """Return OD flow lines for visualization (stub — Phase 5)."""
    return []


# ---- Leaderboard (Phase 6 P1) ----

@api_router.get("/leaderboard/stations", response_model=list[LeaderboardEntryOut])
async def get_leaderboard(
    sort_by: str = "trips",
    limit: int = 10,
):
    """Return station leaderboard sorted by the given metric.

    Args:
        sort_by: Sort dimension — ``"trips"``, ``"revenue"``,
                 ``"profit"``, or ``"achievements"`` (default ``"trips"``).
        limit: Max entries to return (default 10, max 100).
    """
    if limit > 100:
        limit = 100
    if sort_by not in ("trips", "revenue", "profit", "achievements"):
        sort_by = "trips"
    tracker = _engine_mgr.station_stats_tracker
    entries = tracker.get_leaderboard(sort_by=sort_by, limit=limit)  # type: ignore[arg-type]
    return [
        LeaderboardEntryOut(
            station_id=e.station_id,
            trips_completed=e.trips_completed,
            revenue_generated=e.revenue_generated,
            profit_contributed=e.profit_contributed,
            achievement_count=e.achievement_count,
            dispatch_in=e.dispatch_in,
            dispatch_out=e.dispatch_out,
            last_active_tick=e.last_active_tick,
        )
        for e in entries
    ]


@api_router.get("/leaderboard/stations/{station_id}", response_model=StationStatsOut)
async def get_station_stats(station_id: str):
    """Return detailed stats for a single station."""
    from fastapi import HTTPException

    tracker = _engine_mgr.station_stats_tracker
    stats = tracker.get_station_stats(station_id)
    if stats is None:
        raise HTTPException(status_code=404, detail="Station not found")
    return StationStatsOut(
        station_id=stats.station_id,
        trips_completed=stats.trips_completed,
        revenue_generated=stats.revenue_generated,
        profit_contributed=stats.profit_contributed,
        achievement_count=stats.achievement_count,
        dispatch_in=stats.dispatch_in,
        dispatch_out=stats.dispatch_out,
        last_active_tick=stats.last_active_tick,
    )
