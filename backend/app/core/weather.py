"""Weather and environment — dynamic conditions affecting demand & operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from math import exp


class WeatherCondition(Enum):
    CLEAR = auto()
    CLOUDY = auto()
    LIGHT_RAIN = auto()
    HEAVY_RAIN = auto()
    THUNDERSTORM = auto()
    LIGHT_SNOW = auto()
    HEAVY_SNOW = auto()


@dataclass(frozen=True)
class SpecialEvent:
    """A temporary localised event that boosts demand in a zone."""

    event_id: str
    name: str
    zone_id: str
    start_tick: int
    end_tick: int
    demand_multiplier: float = 2.0
    radius_km: float = 1.0

    def is_active(self, tick: int) -> bool:
        return self.start_tick <= tick < self.end_tick


@dataclass
class Environment:
    """Mutable environment state updated each tick."""

    weather: WeatherCondition = WeatherCondition.CLEAR
    temperature_c: float = 20.0
    wind_speed_kmh: float = 0.0
    special_events: dict[str, SpecialEvent] = field(default_factory=dict)

    # ── factors ──────────────────────────────────────────────────────

    def demand_factor(self) -> float:
        """Composite multiplier applied to trip demand (1.0 = normal)."""
        base = _weather_demand_factor(self.weather)
        # Heavy wind and extreme temperatures reduce demand
        if self.temperature_c < -5 or self.temperature_c > 38:
            base *= 0.6
        if self.wind_speed_kmh > 50:
            base *= 0.7
        return base

    def event_factor(self, tick: int, zone_id: str) -> float:
        """Return the demand multiplier from active events in the given zone."""
        factor = 1.0
        for event in self.special_events.values():
            if event.is_active(tick) and event.zone_id == zone_id:
                factor *= event.demand_multiplier
        return factor

    def total_demand_multiplier(self, tick: int, zone_id: str) -> float:
        return self.demand_factor() * self.event_factor(tick, zone_id)


def _weather_demand_factor(condition: WeatherCondition) -> float:
    mapping = {
        WeatherCondition.CLEAR: 1.0,
        WeatherCondition.CLOUDY: 0.9,
        WeatherCondition.LIGHT_RAIN: 0.7,
        WeatherCondition.HEAVY_RAIN: 0.4,
        WeatherCondition.THUNDERSTORM: 0.2,
        WeatherCondition.LIGHT_SNOW: 0.5,
        WeatherCondition.HEAVY_SNOW: 0.2,
    }
    return mapping.get(condition, 1.0)
