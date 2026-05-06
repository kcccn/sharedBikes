"""API v1 router: simulation, city, fleet, and dashboard endpoints."""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    BikeOut,
    CityOut,
    EdgeOut,
    EventOut,
    FleetOut,
    FlowLine,
    HeatmapCell,
    NodeOut,
    SimConfigIn,
    SimStatusOut,
    StationOut,
    ZoneOut,
)
from app.services.map_service import MapService

api_router = APIRouter()
_map_service = MapService()


def _get_city_data(city_name: str = "Beijing") -> CityOut:
    """Build a CityOut response from the MapService."""
    city = _map_service.load_city(city_name)
    nodes_out = [
        NodeOut(
            node_id=n.node_id,
            lat=n.position.lat,
            lng=n.position.lng,
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
            lat=s.position.lat,
            lng=s.position.lng,
            capacity=s.capacity,
            name=s.name,
        )
        for s in city.stations.values()
    ]
    zones_out = [
        ZoneOut(
            zone_id=z.zone_id,
            name=z.name,
            polygon=[(p.lat, p.lng) for p in z.polygon],
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
    city = _map_service.load_city("Beijing")
    return [
        StationOut(
            station_id=s.station_id,
            lat=s.position.lat,
            lng=s.position.lng,
            capacity=s.capacity,
            name=s.name,
        )
        for s in city.stations.values()
    ]


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
