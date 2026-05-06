"""
Demand pattern profiles — how trip volumes vary by time, place, and weather.

The core idea: instead of simulating individual NPCs, we model **demand as a
spatio-temporal intensity field**. At each simulation tick, we sample from
this field to generate RideStarted events.

This approach is:
  • Lightweight — no agent state to track.
  • Analytically tractable — the field is a heatmap, ready for Deck.gl.
  • Easy to tune — adjust curves with simple multipliers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core.clock import SimClock
from ..core.models import DayPhase, WeatherCondition


# ── Time-of-day demand curves ───────────────────────────────────────

# Base trip rate per 1000 population, by hour (weekday)
WEEKDAY_HOURLY_RATE: list[float] = [
    0.5,    # 00:00
    0.3,    # 01:00
    0.2,    # 02:00
    0.1,    # 03:00
    0.2,    # 04:00
    0.8,    # 05:00
    3.0,    # 06:00  ← morning ramp-up
    8.0,    # 07:00  ← Morning Peak
    10.0,   # 08:00  ← Morning Peak zenith
    7.0,    # 09:00
    4.5,    # 10:00
    4.0,    # 11:00
    4.5,    # 12:00  ← midday lunch bump
    4.0,    # 13:00
    4.0,    # 14:00
    4.5,    # 15:00
    5.0,    # 16:00  ← Evening ramp-up
    8.0,    # 17:00  ← Evening Peak
    9.0,    # 18:00  ← Evening Peak zenith
    6.0,    # 19:00
    4.0,    # 20:00
    2.5,    # 21:00
    1.5,    # 22:00
    0.8,    # 23:00
]

# Weekend: flatter, later peaks
WEEKEND_HOURLY_RATE: list[float] = [
    0.3, 0.2, 0.1, 0.1, 0.1, 0.3, 0.8, 2.0,
    3.5, 5.0, 5.5, 6.0, 6.5, 6.0, 5.5, 5.0,
    5.0, 5.5, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0,
]

# ── Weather multipliers ─────────────────────────────────────────────

WEATHER_MULTIPLIER: dict[WeatherCondition, float] = {
    WeatherCondition.CLEAR: 1.0,
    WeatherCondition.CLOUDY: 0.9,
    WeatherCondition.RAIN: 0.5,
    WeatherCondition.HEAVY_RAIN: 0.2,
    WeatherCondition.STORM: 0.05,
    WeatherCondition.EXTREME_HEAT: 0.6,
    WeatherCondition.SNOW: 0.3,
}


@dataclass
class DemandProfile:
    """
    Parameterized demand model for a city.

    The `population_density` field is a dict mapping land-use categories
    to their geographic weight (e.g., residential=0.4, commercial=0.3).
    """
    city_name: str
    total_population: int = 1_000_000
    bike_penetration: float = 0.05       # % of population that uses shared bikes
    commute_ratio: float = 0.6           # fraction of trips that are commute (vs leisure)

    def hourly_rate(self, clock: SimClock, weather: WeatherCondition) -> float:
        """
        Compute expected number of new trips started in this hour.

        This is the **intensity** parameter of a Poisson process.
        """
        hourly = WEEKEND_HOURLY_RATE if clock.is_weekend else WEEKDAY_HOURLY_RATE
        base = hourly[clock.hour_of_day]
        weather_f = WEATHER_MULTIPLIER.get(weather, 0.5)
        return base * self.bike_penetration * self.total_population * weather_f / 100.0

    def phase(self, clock: SimClock) -> DayPhase:
        """Map current clock time to a DayPhase."""
        h = clock.hour_of_day
        for phase in DayPhase:
            lo, hi = phase.value
            if lo <= h < hi:
                return phase
        return DayPhase.NIGHT_DEAD
