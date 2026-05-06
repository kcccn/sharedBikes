"""Weather and environmental conditions affecting simulation."""

from __future__ import annotations

import enum
import random
from dataclasses import dataclass


class WeatherType(enum.Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    STORM = "storm"


@dataclass
class SpecialEvent:
    """A temporary event affecting demand in a zone."""

    event_id: str
    name: str
    zone_id: str
    start_tick: int
    duration_ticks: int
    demand_multiplier: float = 2.0
    radius_km: float = 1.0


@dataclass
class Environment:
    """Current environmental state for a single tick."""

    weather: WeatherType = WeatherType.CLEAR
    temperature_c: float = 20.0
    special_events: list[SpecialEvent] = ()

    def demand_factor(self) -> float:
        """Multiplier applied to baseline demand."""
        f = 1.0
        if self.weather == WeatherType.RAIN:
            f *= 0.6
        elif self.weather == WeatherType.STORM:
            f *= 0.2
        for _event in self.special_events:
            f *= _event.demand_multiplier
        return f


class WeatherGenerator:
    """Incrementally generates weather conditions per tick."""

    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)

    def generate(self, tick: int) -> Environment:
        _ = tick  # tick-based deterministic weather may be added later
        r = self._rng.random()
        if r < 0.6:
            weather = WeatherType.CLEAR
        elif r < 0.85:
            weather = WeatherType.CLOUDY
        elif r < 0.95:
            weather = WeatherType.RAIN
        else:
            weather = WeatherType.STORM
        return Environment(weather=weather, temperature_c=20.0 + self._rng.gauss(0, 5))
