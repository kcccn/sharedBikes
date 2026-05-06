"""Weather and environmental conditions."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum


class WeatherType(Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    STORM = "storm"
    SNOW = "snow"


@dataclass
class SpecialEvent:
    """A temporary high-demand event (concert, festival, ...)."""

    event_id: str
    name: str
    station_id: str
    radius_km: float = 1.0
    demand_multiplier: float = 3.0
    duration_ticks: int = 120
    remaining_ticks: int = 120


@dataclass
class Environment:
    """Simulated weather & events state."""

    weather: WeatherType = WeatherType.CLEAR
    temperature_c: float = 20.0
    wind_speed_kmh: float = 5.0
    special_events: list[SpecialEvent] = field(default_factory=list)

    def randomize(self) -> None:
        self.weather = random.choice(list(WeatherType))
        self.temperature_c = round(random.gauss(18, 8), 1)
        self.wind_speed_kmh = round(random.gauss(10, 5), 1)

    def demand_modifier(self) -> float:
        """Return a multiplier (0…1) for bike demand based on weather."""
        modifiers = {
            WeatherType.CLEAR: 1.0,
            WeatherType.CLOUDY: 0.85,
            WeatherType.RAIN: 0.50,
            WeatherType.STORM: 0.15,
            WeatherType.SNOW: 0.35,
        }
        return modifiers.get(self.weather, 1.0)

    def tick(self) -> None:
        """Advance special-event timers."""
        self.special_events = [
            e for e in self.special_events if e.remaining_ticks > 0
        ]
        for e in self.special_events:
            e.remaining_ticks -= 1
