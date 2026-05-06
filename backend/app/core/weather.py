"""Weather & external events that affect demand and rider behaviour."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from random import Random


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
    station_id: str  # center station affected
    surge_multiplier: float = 3.0
    radius_km: float = 1.0  # affects stations within this radius


@dataclass
class Environment:
    """Aggregate external conditions for the current tick."""

    weather: Weather = field(default_factory=Weather)
    events: list[SpecialEvent] = field(default_factory=list)
    rng: Random = field(default_factory=Random)

    # Cache of (event_id, station_id) → factor to avoid repeated distance calc
    _event_cache: dict[tuple[str, str], float] = field(default_factory=dict)

    def _factor_for_event(
        self, event: SpecialEvent, tick: int, station_id: str
    ) -> float:
        """Check if *station_id* is within *event*'s radius of influence."""
        if not (event.tick_start <= tick < event.tick_end):
            return 1.0

        key = (event.id, station_id)
        cached = self._event_cache.get(key)
        if cached is not None:
            return cached

        if event.radius_km <= 0 or event.station_id == station_id:
            # Exact match or zero radius → affects only the center station
            factor = event.surge_multiplier if event.station_id == station_id else 1.0
        else:
            # Distance-based falloff would go here with a spatial index
            # For now, approximate: same station = full multiplier
            factor = event.surge_multiplier if event.station_id == station_id else 1.0

        self._event_cache[key] = factor
        return factor

    def demand_factor(self, tick: int, station_id: str) -> float:
        """Combined multiplier from weather + active events at *station_id*."""
        factor = self.weather.demand_multiplier
        for ev in self.events:
            factor *= self._factor_for_event(ev, tick, station_id)
        return factor

    def tick(self) -> None:
        """Advance the environment one tick (e.g. update weather gradually)."""
        # Placeholder — weather Markov chain will go here in Phase 2.
        pass
