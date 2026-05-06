"""Pydantic models / DTOs for API serialisation."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error envelope returned by all API endpoints."""

    code: str
    detail: str


class HealthResponse(BaseModel):
    status: str
    version: str


class CityResponse(BaseModel):
    id: str
    name: str
    station_count: int
    zone_count: int


class StationResponse(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    capacity: int
    inventory: int


class FleetSnapshotResponse(BaseModel):
    total_bikes: int
    active_rides: int
    lost_bikes: int
    station_inventory: dict[str, int]


class SimulationStatusResponse(BaseModel):
    state: str
    tick: int
    time_of_day: str


class HeatmapPoint(BaseModel):
    lat: float
    lng: float
    intensity: float


class HeatmapResponse(BaseModel):
    tick: int
    points: list[HeatmapPoint]


class FlowLine(BaseModel):
    from_lat: float
    from_lng: float
    to_lat: float
    to_lng: float
    volume: int


class FlowResponse(BaseModel):
    tick: int
    flows: list[FlowLine]
