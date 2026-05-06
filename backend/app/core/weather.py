"""Weather & environment domain model."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable

from app.core.city import LatLng


class WeatherType(Enum):
    CLEAR = auto()
    CLOUDY = auto()
    RAINY = auto()
    STORMY = auto()


@dataclass
class Weather:
    """Current weather conditions affecting rider demand."""

    weather_type: WeatherType = WeatherType.CLEAR
    temperature_c: float = 20.0
    wind_speed_kmh: float = 0.0
    precipitation_mm: float = 0.0

    def demand_multiplier(self) -> float:
        """Factor by which rider demand is scaled (0.0 – 1.0)."""
        if self.weather_type == WeatherType.STORMY:
            return 0.05
        if self.weather_type == WeatherType.RAINY:
            return 0.40
        if self.weather_type == WeatherType.CLOUDY:
            return 0.85
        return 1.0


@dataclass
class SpecialEvent:
    """A temporary event affecting a geographic area (concert, festival, etc.)."""

    event_id: str
    name: str
    center: LatLng
    radius_km: float
    demand_surge: float  # multiplier, e.g. 2.5 = 250 % demand
    duration_ticks: int
    remaining_ticks: int

    def is_active(self) -> bool:
        return self.remaining_ticks > 0

    def factor_at(self, pos: LatLng) -> float:
        """Return the demand multiplier at *pos*, decaying with distance."""
        if not self.is_active():
            return 1.0
        d = _haversine(
            self.center.lat, self.center.lng, pos.lat, pos.lng
        )
        if d > self.radius_km:
            return 1.0
        # linear decay from center (full surge) to edge (1.0)
        decay = d / self.radius_km if self.radius_km > 0 else 0.0
        return 1.0 + (self.demand_surge - 1.0) * (1.0 - decay)

    def tick(self) -> None:
        if self.remaining_ticks > 0:
            self.remaining_ticks -= 1


@dataclass
class Environment:
    """Aggregate environment state."""

    weather: Weather = field(default_factory=Weather)
    events: dict[str, SpecialEvent] = field(default_factory=dict)
    time_of_day: str = "00:00"  # HH:MM

    def demand_multiplier_at(self, pos: LatLng) -> float:
        """Combined demand modifier (weather × active events)."""
        m = self.weather.demand_multiplier()
        for event in self.events.values():
            m *= event.factor_at(pos)
        return m

    def tick_events(self) -> None:
        for event in list(self.events.values()):
            event.tick()
            if not event.is_active():
                del self.events[event.event_id]


_EARTH_RADIUS_KM = 6371.0


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great‑circle distance in km."""
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return _EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
