"""Weather & environmental conditions model."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import NamedTuple


class WeatherCondition(Enum):
    CLEAR = auto()
    CLOUDY = auto()
    RAIN = auto()
    STORM = auto()
    SNOW = auto()


@dataclass
class SpecialEvent:
    """A temporary event that affects demand in a region."""

    id: str
    name: str
    centre_lat: float
    centre_lng: float
    radius_km: float
    demand_multiplier: float = 2.0
    start_tick: int = 0
    end_tick: int = 60


@dataclass
class Environment:
    """The current environmental state of the simulation."""

    condition: WeatherCondition = WeatherCondition.CLEAR
    temperature_c: float = 20.0
    wind_speed_kmh: float = 0.0
    precipitation_mm: float = 0.0
    special_events: list[SpecialEvent] = field(default_factory=list)

    def demand_factor(self) -> float:
        """Return a multiplier [0, 1] representing how weather suppresses demand."""
        factor = 1.0
        if self.condition == WeatherCondition.RAIN:
            factor *= 0.5
        elif self.condition == WeatherCondition.STORM:
            factor *= 0.15
        elif self.condition == WeatherCondition.SNOW:
            factor *= 0.3
        elif self.condition == WeatherCondition.CLOUDY:
            factor *= 0.9
        return max(factor, 0.0)

    def event_factor_at(self, lat: float, lng: float) -> float:
        """Return the compound demand multiplier for all active events at (lat, lng)."""
        factor = 1.0
        for event in self.special_events:
            d = self._haversine(lat, lng, event.centre_lat, event.centre_lng)
            if d <= event.radius_km:
                factor *= event.demand_multiplier
        return factor

    @staticmethod
    def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Great-circle distance in km between two lat/lng points."""
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlng / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
