"""
Domain events — the single source of truth for the simulation.

Every state change in the simulation is recorded as an immutable event.
The world state at time T is `fold(events[0..T])`.

This makes possible:
  • Time-travel debugging: replay from genesis to any checkpoint.
  • OD flow visualization: each RideCompleted is a trip with origin, dest, timestamp.
  • Snapshot isolation: periodic snapshots for efficient queries.
  • Audit: every decision (player or algorithm) is captured.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from .models import BikeStatus, GeoPoint, VehicleType, WeatherCondition


# ── Event protocol ───────────────────────────────────────────────────

class SimEvent(Protocol):
    """Marker protocol for all domain events."""
    timestamp: datetime
    event_type: str


# ── Concrete events ──────────────────────────────────────────────────

@dataclass
class SimulationStarted:
    """The simulation was initialized with a given seed and config."""
    timestamp: datetime
    event_type: str = "simulation_started"
    seed: int = 0
    city_name: str = ""
    bounds: tuple[float, float, float, float] | None = None   # min_lat, min_lng, max_lat, max_lng


@dataclass
class BikeDeployed:
    """A new bike enters service at a location."""
    timestamp: datetime
    bike_id: str
    position: GeoPoint
    event_type: str = "bike_deployed"


@dataclass
class StationCreated:
    """Player or game logic establishes a station (P点 / forbidden / dock)."""
    timestamp: datetime
    station_id: str
    event_type: str = "station_created"


@dataclass
class RideStarted:
    """A user picks up a bike. This is the origin of an OD pair."""
    timestamp: datetime
    ride_id: str
    bike_id: str
    origin: GeoPoint
    user_id: str = ""
    event_type: str = "ride_started"


@dataclass
class RideCompleted:
    """A user drops off a bike. This completes the OD pair."""
    timestamp: datetime
    ride_id: str
    bike_id: str
    destination: GeoPoint
    distance_km: float
    duration_min: float
    revenue: float
    event_type: str = "ride_completed"


@dataclass
class BikeStatusChanged:
    """Bike reported lost, broken, or found."""
    timestamp: datetime
    bike_id: str
    old_status: BikeStatus
    new_status: BikeStatus
    event_type: str = "bike_status_changed"


@dataclass
class RebalanceTripStarted:
    """A rebalancing vehicle departs with a load of bikes."""
    timestamp: datetime
    vehicle_id: str
    origin: GeoPoint
    bikes_on_board: list[str]
    event_type: str = "rebalance_trip_started"


@dataclass
class RebalanceTripCompleted:
    """A rebalancing vehicle drops off bikes at destination."""
    timestamp: datetime
    vehicle_id: str
    destination: GeoPoint
    bikes_dropped: list[str]
    event_type: str = "rebalance_trip_completed"


@dataclass
class WeatherChanged:
    """Weather condition changes, affecting demand multipliers."""
    timestamp: datetime
    condition: WeatherCondition
    event_type: str = "weather_changed"


@dataclass
class SpecialEventOccurred:
    """A temporal event (concert, holiday, sports) that spikes local demand."""
    timestamp: datetime
    event_id: str
    location: GeoPoint
    radius_km: float
    demand_multiplier: float
    duration_hours: float
    name: str = ""
    event_type: str = "special_event_occurred"


@dataclass
class DayAdvanced:
    """Simulation clock tick — time moves forward."""
    timestamp: datetime
    elapsed_hours: float
    event_type: str = "day_advanced"


@dataclass
class SnapshotTaken:
    """Periodic snapshot of aggregate state for efficient queries."""
    timestamp: datetime
    snapshot_id: str
    bike_positions: dict[str, GeoPoint]
    station_loads: dict[str, int]
    balance: float
    event_type: str = "snapshot_taken"
