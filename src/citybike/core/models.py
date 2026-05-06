"""
Domain models — pure data, zero I/O.
All coordinates use (lat, lng) float tuples.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import NamedTuple


# ── Value Objects ────────────────────────────────────────────────────

class GeoPoint(NamedTuple):
    """A point on the earth surface in WGS84."""
    lat: float
    lng: float


class GeoBounds(NamedTuple):
    """Axis-aligned bounding box in lat/lng space."""
    min_lat: float
    min_lng: float
    max_lat: float
    max_lng: float


# ── Enums ────────────────────────────────────────────────────────────

class BikeStatus(Enum):
    AVAILABLE = auto()
    IN_USE = auto()
    REPORTED_LOST = auto()
    REPORTED_BROKEN = auto()


class StationType(Enum):
    """Regulatory station types a player can interact with."""
    RECOMMENDED = "R"       # Recommended parking point (P点)
    FORBIDDEN = "F"         # No-parking zone
    DOCK_STATION = "D"      # Docked station


class WeatherCondition(Enum):
    CLEAR = auto()
    CLOUDY = auto()
    RAIN = auto()
    HEAVY_RAIN = auto()
    STORM = auto()
    EXTREME_HEAT = auto()
    SNOW = auto()


class DayPhase(Enum):
    """Six time windows that drive demand patterns."""
    EARLY_MORNING = (0, 6)       # 00:00-06:00 — dead zone
    MORNING_PEAK = (6, 9)        # 06:00-09:00 — inbound commuters
    MIDDAY = (9, 16)             # 09:00-16:00 — errand / leisure
    EVENING_PEAK = (16, 19)      # 16:00-19:00 — outbound commuters
    NIGHT_ACTIVE = (19, 23)      # 19:00-23:00 — entertainment
    NIGHT_DEAD = (23, 24)        # 23:00-00:00 — minimal


# ── Entity: Bike ─────────────────────────────────────────────────────

@dataclass
class Bike:
    """A single shared bike with its lifecycle state."""
    bike_id: str = field(default_factory=lambda: f"bike_{uuid.uuid4().hex[:8]}")
    status: BikeStatus = BikeStatus.AVAILABLE
    position: GeoPoint | None = None          # current lat/lng
    total_rides: int = 0
    total_distance_km: float = 0.0
    last_service_at: datetime | None = None


# ── Entity: Station ──────────────────────────────────────────────────

@dataclass
class Station:
    """A designated location: recommended parking, dock, or forbidden zone."""
    station_id: str
    station_type: StationType
    position: GeoPoint
    capacity: int = 20          # for DOCK / RECOMMENDED
    name: str = ""


# ── Entity: Rebalancing Vehicle ──────────────────────────────────────

class VehicleType(Enum):
    CARGO_TRICYCLE = "tricycle"      # small, narrow streets
    VAN = "van"                      # large, main roads only


@dataclass
class RebalanceVehicle:
    vehicle_id: str
    vehicle_type: VehicleType
    capacity: int                     # how many bikes it can carry
    position: GeoPoint
    route: list[GeoPoint] = field(default_factory=list)
    cargo: int = 0
