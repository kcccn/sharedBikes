"""Satisfaction tracker — monitors station health and drives demand feedback.

Tracks per-station satisfaction based on:
- Hours spent empty (no bikes available)
- Hours spent full (no docks available)
- Missed returns (NPC tried to return bike, station was full)
- Missed pickups (NPC tried to pick up bike, station was empty)

Satisfaction decays when station is unhealthy and recovers slowly
when the station returns to normal operation.

Phase D (v0.4): Satisfaction feeds back into demand generation —
low satisfaction reduces trip generation at that station, and
very low satisfaction causes NPC churn.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StationHealth:
    """Health snapshot for a single station at a point in time."""

    station_id: str
    satisfaction: float = 1.0          # 0.0..1.0
    hours_empty: int = 0               # cumulative hours with 0 bikes
    hours_full: int = 0                # cumulative hours with 0 docks
    missed_returns: int = 0            # NPC tried to return, station full
    missed_pickups: int = 0            # NPC tried to pick up, station empty


# ── decay/recovery rates (per tick ≈ per minute) ────────────────

_SATISFACTION_DECAY_PER_TICK_EMPTY = 0.002   # ~3 days to go from 1.0 → 0.0 if always empty
_SATISFACTION_DECAY_PER_TICK_FULL = 0.001    # full is less damaging than empty
_SATISFACTION_RECOVERY_PER_TICK = 0.0005     # ~1.5 days to recover from 0.0 → 1.0
_SATISFACTION_CHURN_THRESHOLD = 0.3          # below this → demand reduction
_SATISFACTION_CRITICAL_THRESHOLD = 0.15      # below this → NPC churn alert


class SatisfactionTracker:
    """Tracks satisfaction per station, updated every tick.

    Usage (in game loop):
        tracker = SatisfactionTracker(station_ids)
        # ... after each tick ...
        tracker.update(inventory, capacity, missed_returns, missed_pickups)
        demand_multipliers = tracker.demand_multipliers()  # for demand scaling
    """

    def __init__(self, station_ids: list[str]) -> None:
        self._stations: dict[str, StationHealth] = {
            sid: StationHealth(station_id=sid) for sid in station_ids
        }

    @property
    def all_health(self) -> dict[str, StationHealth]:
        """Return a copy of all station health snapshots."""
        return dict(self._stations)

    def get_health(self, station_id: str) -> StationHealth | None:
        """Return health for a specific station, or None if unknown."""
        return self._stations.get(station_id)

    def update(
        self,
        inventory: dict[str, int],
        capacity: dict[str, int],
        missed_returns: dict[str, int] | None = None,
        missed_pickups: dict[str, int] | None = None,
    ) -> None:
        """Advance satisfaction state by one tick.

        Args:
            inventory: Current bike inventory per station_id.
            capacity: Current dock capacity per station_id.
            missed_returns: Count of missed returns per station_id (optional).
            missed_pickups: Count of missed pickups per station_id (optional).
        """
        for sid, health in self._stations.items():
            inv = inventory.get(sid, 0)
            cap = capacity.get(sid, 1)  # avoid division by zero

            is_empty = inv == 0
            is_full = inv >= cap

            # Decay
            if is_empty:
                health.satisfaction = max(0.0, health.satisfaction - _SATISFACTION_DECAY_PER_TICK_EMPTY)
                health.hours_empty += 1
            elif is_full:
                health.satisfaction = max(0.0, health.satisfaction - _SATISFACTION_DECAY_PER_TICK_FULL)
                health.hours_full += 1
            else:
                # Recovery when healthy
                health.satisfaction = min(1.0, health.satisfaction + _SATURATION_RECOVERY_PER_TICK)

            # Missed events (each missed event is a significant satisfaction hit)
            if missed_returns:
                n_returns = missed_returns.get(sid, 0)
                if n_returns > 0:
                    health.missed_returns += n_returns
                    # Each missed return costs 0.01 satisfaction
                    health.satisfaction = max(0.0, health.satisfaction - 0.01 * n_returns)

            if missed_pickups:
                n_pickups = missed_pickups.get(sid, 0)
                if n_pickups > 0:
                    health.missed_pickups += n_pickups
                    # Each missed pickup costs 0.01 satisfaction
                    health.satisfaction = max(0.0, health.satisfaction - 0.01 * n_pickups)

    def demand_multiplier(self, station_id: str) -> float:
        """Return a demand multiplier for *station_id* based on satisfaction.

        Returns 1.0 for healthy stations, decreasing toward 0.0 as
        satisfaction drops below the churn threshold.
        """
        health = self._stations.get(station_id)
        if health is None:
            return 1.0

        sat = health.satisfaction
        if sat >= _SATURATION_CHURN_THRESHOLD:
            return 1.0
        if sat <= _SATURATION_CRITICAL_THRESHOLD:
            return 0.0
        # Linear interpolation between thresholds
        t = (sat - _SATURATION_CRITICAL_THRESHOLD) / (
            _SATURATION_CHURN_THRESHOLD - _SATURATION_CRITICAL_THRESHOLD
        )
        return max(0.0, t)

    def demand_multipliers(self) -> dict[str, float]:
        """Return demand multipliers for all tracked stations."""
        return {sid: self.demand_multiplier(sid) for sid in self._stations}

    @property
    def average_satisfaction(self) -> float:
        """Average satisfaction across all stations."""
        if not self._stations:
            return 1.0
        return sum(h.satisfaction for h in self._stations.values()) / len(self._stations)

    @property
    def critical_stations(self) -> list[str]:
        """Stations with satisfaction below critical threshold."""
        return [
            sid for sid, h in self._stations.items()
            if h.satisfaction < _SATURATION_CRITICAL_THRESHOLD
        ]

    @property
    def warning_stations(self) -> list[str]:
        """Stations with satisfaction below warning threshold (but not critical)."""
        return [
            sid for sid, h in self._stations.items()
            if _SATURATION_CRITICAL_THRESHOLD <= h.satisfaction < _SATURATION_CHURN_THRESHOLD
        ]
