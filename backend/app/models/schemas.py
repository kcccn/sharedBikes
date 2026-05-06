"""Pydantic schemas for API I/O."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str


# ── City ─────────────────────────────────────────────────

class StationResponse(BaseModel):
    station_id: str
    name: str
    lat: float
    lng: float
    capacity: int


class CityResponse(BaseModel):
    node_count: int
    edge_count: int
    station_count: int
    zone_count: int


# ── Fleet ────────────────────────────────────────────────

class FleetSnapshotResponse(BaseModel):
    total_bikes: int
    docked: int
    in_use: int
    lost: int
    maintenance: int
    station_counts: dict[str, int]


class BikeResponse(BaseModel):
    bike_id: str
    status: str
    station_id: str | None = None
    total_trips: int
    total_distance_km: float


# ── Simulation ──────────────────────────────────────────

class SimulationStatusResponse(BaseModel):
    state: str
    tick: int
    time_of_day: str
    fleet: FleetSnapshotResponse | None = None


class SimulationActionResponse(BaseModel):
    message: str
    state: str


# ── Dashboard ────────────────────────────────────────────

class HeatmapCell(BaseModel):
    lat: float
    lng: float
    intensity: float


class HeatmapResponse(BaseModel):
    cells: list[HeatmapCell]
    generated_at: str


class FlowLine(BaseModel):
    from_lat: float
    from_lng: float
    to_lat: float
    to_lng: float
    volume: int


class FlowResponse(BaseModel):
    flows: list[FlowLine]
    generated_at: str


# ── Error ────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    code: str
    detail: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
