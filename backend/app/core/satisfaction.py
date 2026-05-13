"""Satisfaction & Station Health tracking.

Phase D (v0.4): Station satisfaction tracks how well a station serves NPCs.
Low satisfaction reduces demand generation at that station. Very low
satisfaction can lead to NPC churn.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.city import Station


# ── Satisfaction thresholds ─────────────────────────────────────

SATISFACTION_MAX = 1.0
SATISFACTION_MIN = 0.0
SATISFACTION_GOOD = 0.7  # above this = healthy
SATISFACTION_WARN = 0.4  # below this = warning
SATISFACTION_CRITICAL = 0.2  # below this = churn risk

DECAY_PER_TICK_EMPTY = 0.002  # satisfaction lost per tick when empty
DECAY_PER_TICK_FULL = 0.001  # satisfaction lost per tick when full
RECOVERY_PER_TICK_HEALTHY = 0.0005  # recovery per tick when healthy


@dataclass
class StationHealth:
    """Health metrics for a single station.

    Attributes:
        station_id: Station identifier.
        satisfaction: Current satisfaction level [0.0, 1.0].
        hours_empty: Cumulative hours the station has been empty.
        hours_full: Cumulative hours the station has been full.
        missed_returns: Count of NPCs that tried to return a bike but station was full.
        missed_pickups: Count of NPCs that tried to pick up a bike but station was empty.
    """

    station_id: str
    satisfaction: float = SATISFACTION_MAX
    hours_empty: int = 0
    hours_full: int = 0
    missed_returns: int = 0
    missed_pickups: int = 0

    @property
    def is_healthy(self) -> bool:
        return self.satisfaction >= SATISFACTION_GOOD

    @property
    def is_warning(self) -> bool:
        return SATISFACTION_WARN <= self.satisfaction < SATISFACTION_GOOD

    @property
    def is_critical(self) -> bool:
        return self.satisfaction < SATISFACTION_CRITICAL

    @property
    def demand_factor(self) -> float:
        """Return a demand multiplier based on satisfaction.

        - satisfaction >= 0.7: 1.0 (full demand)
        - 0.4 <= satisfaction < 0.7: linear interpolation 1.0 → 0.5
        - 0.2 <= satisfaction < 0.4: linear interpolation 0.5 → 0.2
        - satisfaction < 0.2: 0.1 (minimal demand)
        """
        if self.satisfaction >= SATISFACTION_GOOD:
            return 1.0
        if self.satisfaction >= SATISFACTION_WARN:
            # 0.4 ~ 0.7 → 0.5 ~ 1.0
            t = (self.satisfaction - SATISFACTION_WARN) / (SATISFACTION_GOOD - SATISFACTION_WARN)
            return 0.5 + 0.5 * t
        if self.satisfaction >= SATISFACTION_CRITICAL:
            # 0.2 ~ 0.4 → 0.2 ~ 0.5
            t = (self.satisfaction - SATISFACTION_CRITICAL) / (SATISFACTION_WARN - SATISFACTION_CRITICAL)
            return 0.2 + 0.3 * t
        return 0.1


@dataclass
class SatisfactionTracker:
    """Tracks satisfaction for all stations in the city.

    Updates per tick based on station inventory levels. Provides
    demand factor multipliers to the trip generator.
    """

    health: dict[str, StationHealth] = field(default_factory=dict)

    @classmethod
    def from_stations(cls, stations: dict[str, Station]) -> SatisfactionTracker:
        """Create a SatisfactionTracker initialised with all city stations."""
        return cls(
            health={
                sid: StationHealth(station_id=sid)
                for sid in stations
            }
        )

    def get_health(self, station_id: str) -> StationHealth | None:
        """Return StationHealth for a given station, or None if unknown."""
        return self.health.get(station_id)

    def get_demand_factor(self, station_id: str) -> float:
        """Return the demand multiplier for a station based on its satisfaction."""
        h = self.health.get(station_id)
        if h is None:
            return 1.0
        return h.demand_factor

    def get_all_demand_factors(self) -> dict[str, float]:
        """Return demand factors for all tracked stations."""
        return {
            sid: h.demand_factor
            for sid, h in self.health.items()
        }

    def update(
        self,
        tick: int,
        station_inventory: dict[str, int],
        station_capacity: dict[str, int],
    ) -> None:
        """Update satisfaction metrics for all stations for this tick.

        Called once per tick after trip execution and before rebalancing.

        Args:
            tick: Current simulation tick.
            station_inventory: Current bike count per station.
            station_capacity: Max capacity per station.
        """
        # Every 60 ticks ≈ 1 sim-hour, update satisfaction
        if tick % 60 != 0:
            return

        for sid, health in self.health.items():
            inv = station_inventory.get(sid, 0)
            cap = station_capacity.get(sid, 0)

            if cap <= 0:
                continue

            ratio = inv / cap

            if ratio <= 0.0:
                # Station is empty — decay satisfaction
                health.satisfaction = max(
                    SATISFACTION_MIN,
                    health.satisfaction - DECAY_PER_TICK_EMPTY,
                )
                health.hours_empty += 1
            elif ratio >= 1.0:
                # Station is full — slight decay
                health.satisfaction = max(
                    SATISFACTION_MIN,
                    health.satisfaction - DECAY_PER_TICK_FULL,
                )
                health.hours_full += 1
            elif 0.2 <= ratio <= 0.8:
                # Healthy range — recover satisfaction
                health.satisfaction = min(
                    SATISFACTION_MAX,
                    health.satisfaction + RECOVERY_PER_TICK_HEALTHY,
                )

    def record_missed_return(self, station_id: str) -> None:
        """Record that an NPC failed to return a bike because station was full."""
        h = self.health.get(station_id)
        if h is not None:
            h.missed_returns += 1
            h.satisfaction = max(
                SATISFACTION_MIN,
                h.satisfaction - DECAY_PER_TICK_EMPTY * 2,
            )

    def record_missed_pickup(self, station_id: str) -> None:
        """Record that an NPC failed to pick up a bike because station was empty."""
        h = self.health.get(station_id)
        if h is not None:
            h.missed_pickups += 1
            h.satisfaction = max(
                SATISFACTION_MIN,
                h.satisfaction - DECAY_PER_TICK_FULL * 2,
            )

    def summary(self) -> dict[str, dict]:
        """Return a summary dict for WS broadcast / debugging."""
        return {
            sid: {
                "satisfaction": round(h.satisfaction, 3),
                "hours_empty": h.hours_empty,
                "hours_full": h.hours_full,
                "missed_returns": h.missed_returns,
                "missed_pickups": h.missed_pickups,
                "demand_factor": round(h.demand_factor, 3),
            }
            for sid, h in self.health.items()
        }
