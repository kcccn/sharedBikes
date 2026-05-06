"""Weather & external events that affect demand and rider behaviour."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from random import Random
from typing import Callable


class WeatherType(Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    STORM = "storm"
    EXTREME = "extreme"  # typhoon / blizzard — no rides


@dataclass
class Weather:
    weather_type: WeatherType = WeatherType.CLEAR
    temperature_c: float = 25.0
    precipitation_mm: float = 0.0
    wind_speed_kmh: float = 0.0

    @property
    def demand_multiplier(self) -> float:
        """How weather affects willingness to ride (1.0 = baseline)."""
        match self.weather_type:
            case WeatherType.CLEAR:
                return 1.0
            case WeatherType.CLOUDY:
                return 0.85
            case WeatherType.RAIN:
                return 0.40
            case WeatherType.STORM:
                return 0.10
            case WeatherType.EXTREME:
                return 0.0


@dataclass
class SpecialEvent:
    """A scheduled one-off event (concert, festival, sports match)."""

    id: str
    name: str
    tick_start: int
    tick_end: int
    station_id: str  # affected station
    surge_multiplier: float = 3.0
    radius_km: float = 1.0


@dataclass
class Environment:
    """Aggregate external conditions for the current tick."""

    weather: Weather = field(default_factory=Weather)
    events: list[SpecialEvent] = field(default_factory=list)
    rng: Random = field(default_factory=Random)

    def demand_factor(self, tick: int, station_id: str) -> float:
        """Combined multiplier from weather + active events at *station_id*."""
        factor = self.weather.demand_multiplier
        for ev in self.events:
            if ev.tick_start <= tick < ev.tick_end and ev.station_id == station_id:
                factor *= ev.surge_multiplier
        return factor

    def tick(self) -> None:
        """Advance the environment one tick (e.g. update weather gradually)."""
        # Placeholder — weather Markov chain will go here in Phase 2.
        pass
