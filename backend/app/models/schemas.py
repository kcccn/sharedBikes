"""Pydantic DTOs for API request/response."""

from pydantic import BaseModel


# ---- City ----

class StationOut(BaseModel):
    station_id: str
    lat: float
    lng: float
    capacity: int
    name: str
    available_bikes: int


class CityOut(BaseModel):
    name: str
    station_count: int
    zone_count: int


# ---- Fleet ----

class BikeOut(BaseModel):
    bike_id: str
    status: str
    station_id: str | None = None
    lat: float | None = None
    lng: float | None = None


class FleetOut(BaseModel):
    total_bikes: int
    active_rides: int
    lost_bikes: int
    bikes: list[BikeOut]


# ---- Simulation ----

class SimStatusOut(BaseModel):
    tick: int
    state: str
    time_of_day: str


class SimConfigIn(BaseModel):
    ticks_per_day: int = 1440
    speed_multiplier: int = 60


# ---- Events ----

class EventOut(BaseModel):
    event_id: str
    name: str
    zone_id: str
    start_tick: int
    duration_ticks: int
    demand_multiplier: float


# ---- Dashboard ----

class HeatmapCell(BaseModel):
    lat: float
    lng: float
    intensity: float


class FlowLine(BaseModel):
    from_lat: float
    from_lng: float
    to_lat: float
    to_lng: float
    volume: int
