"""Pydantic schemas — API-facing DTOs, not domain entities."""

from __future__ import annotations

from pydantic import BaseModel


class LatLngSchema(BaseModel):
    lat: float
    lng: float


class StationSchema(BaseModel):
    id: str
    position: LatLngSchema
    capacity: int
    available_bikes: int = 0
    zone_id: str | None = None


class FleetStatusSchema(BaseModel):
    total_bikes: int
    active_bikes: int
    utilisation_rate: float


class SimulationStateSchema(BaseModel):
    tick: int
    time_of_day: str
    day: int
    state: str
    speed_multiplier: float


class HeatmapCell(BaseModel):
    lat: float
    lng: float
    intensity: float  # 0.0 … 1.0 normalised demand/supply ratio


class HeatmapSchema(BaseModel):
    cells: list[HeatmapCell]


class ODFlowSchema(BaseModel):
    from_station: str
    to_station: str
    volume: int
    colour_hex: str = "#00ff88"
