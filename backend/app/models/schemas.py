"""Pydantic DTOs for API responses."""

from pydantic import BaseModel


class FleetSnapshotResponse(BaseModel):
    total_bikes: int
    active_trips: int
    bikes_docked: int
    utilization: float
    station_inventory: dict[str, int]


class SimulationStatusResponse(BaseModel):
    state: str
    tick: int
    sim_day: int
    time_of_day: str


class StationSummary(BaseModel):
    station_id: str
    name: str
    lat: float
    lng: float
    capacity: int
    current_bikes: int


class EventSchema(BaseModel):
    event_id: str
    name: str
    station_id: str
    demand_multiplier: float
    remaining_ticks: int


class CitySummary(BaseModel):
    name: str
    station_count: int
    zone_count: int
    node_count: int
    edge_count: int
