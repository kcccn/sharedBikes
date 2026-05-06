"""Pydantic schemas for API request / response models."""

from datetime import datetime
from pydantic import BaseModel


class LatLngSchema(BaseModel):
    lat: float
    lng: float


class StationSchema(BaseModel):
    id: str
    name: str
    position: LatLngSchema
    capacity: int
    available_bikes: int


class BikeSchema(BaseModel):
    id: str
    status: str
    station_id: str | None = None
    trip_count: int = 0


class SimulationStatus(BaseModel):
    state: str
    tick: int
    time_of_day: str
    started_at: datetime | None = None


class FleetBalanceSchema(BaseModel):
    starving_stations: list[str]
    overflowing_stations: list[str]
    total_orders: int
