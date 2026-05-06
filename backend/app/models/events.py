"""Event schemas — state-change payloads for WebSocket / event bus."""

from __future__ import annotations

from pydantic import BaseModel


class BikeDockedEvent(BaseModel):
    bike_id: str
    station_id: str
    tick: int


class BikeUndockedEvent(BaseModel):
    bike_id: str
    station_id: str
    tick: int


class TripCompletedEvent(BaseModel):
    bike_id: str
    from_station: str
    to_station: str
    duration_ticks: int
    distance_km: float
    tick: int


class RebalanceTriggeredEvent(BaseModel):
    orders: list[dict]  # simplified; full DispatchOrder schema later
    tick: int
