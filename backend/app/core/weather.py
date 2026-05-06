"""Weather and environmental conditions affecting simulation."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto


class WeatherCondition(Enum):
    CLEAR = auto()
    CLOUDY = auto()
    RAINY = auto()
    STORMY = auto()
    SNOWY = auto()


@dataclass
class SpecialEvent:
    """A one-off event that influences demand (concert, festival, etc.)."""

    event_id: str
    name: str
    station_id: str
    radius_km: float
    demand_multiplier: float = 2.0
    duration_ticks: int = 120
    remaining_ticks: int = 120

    @property
    def active(self) -> bool:
        return self.remaining_ticks > 0

    def tick(self) -> None:
        if self.remaining_ticks > 0:
            self.remaining_ticks -= 1


@dataclass
class Environment:
    """Weather + events affecting the city at a given tick."""

    condition: WeatherCondition = WeatherCondition.CLEAR
    temperature_c: float = 25.0
    wind_speed_kmh: float = 0.0
    events: dict[str, SpecialEvent] = field(default_factory=dict)

    def demand_factor(self) -> float:
        """Overall multiplier applied to base demand (1.0 = normal)."""
        base = 1.0
        if self.condition in (WeatherCondition.RAINY, WeatherCondition.STORMY):
            base *= 0.4
        elif self.condition == WeatherCondition.SNOWY:
            base *= 0.2
        return base

    def tick(self) -> None:
        """Advance environment one tick (random weather drift, event decay)."""
        if random.random() < 0.01:  # ~1 % chance of change per tick
            self.condition = random.choice(list(WeatherCondition))
        for event in list(self.events.values()):
            event.tick()
            if not event.active:
                del self.events[event.event_id]
