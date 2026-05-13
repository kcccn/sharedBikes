"""NPC model — commuter agents with home/work stations and daily schedules.

Each NPC has a home (near residential zone) and work (near commercial zone)
station assignment, producing a realistic daily commute pattern.

Phase D (v0.4): Adds NPC identity to trip generation, enabling:
- Morning/evening commute peaks with directional flow
- Satisfaction-driven churn (NPCs move to competitor if unhappy)
- Cost vs satisfaction trade-off for player decisions
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.city import City


# ── schedule constants ──────────────────────────────────────────

_MORNING_COMMUTE_START = 360   # 06:00
_MORNING_COMMUTE_END = 480     # 08:00
_WORK_START = 480              # 08:00
_WORK_END = 1020               # 17:00
_EVENING_COMMUTE_START = 1020  # 17:00
_EVENING_COMMUTE_END = 1140    # 19:00


@dataclass(frozen=True)
class NPC:
    """A single commuter agent in the simulation.

    Each NPC has a fixed home and work station, producing predictable
    commute trips during peak hours and random leisure trips off-peak.
    """

    id: str
    home_station: str
    work_station: str

    def destination_at(self, tick_of_day: int) -> str | None:
        """Return the NPC's desired destination station at *tick_of_day*.

        Returns None if the NPC should not be generating a trip
        (e.g. midday while already at work).
        """
        if _MORNING_COMMUTE_START <= tick_of_day < _MORNING_COMMUTE_END:
            # Morning: home → work
            return self.work_station
        elif _EVENING_COMMUTE_START <= tick_of_day < _EVENING_COMMUTE_END:
            # Evening: work → home
            return self.home_station
        return None

    def is_commuting(self, tick_of_day: int) -> bool:
        """Whether this NPC is in a commute window at *tick_of_day*."""
        return (
            _MORNING_COMMUTE_START <= tick_of_day < _MORNING_COMMUTE_END
            or _EVENING_COMMUTE_START <= tick_of_day < _EVENING_COMMUTE_END
        )

    def is_at_work(self, tick_of_day: int) -> bool:
        """Whether this NPC is at their work station at *tick_of_day*."""
        return _WORK_START <= tick_of_day < _WORK_END

    def is_at_home(self, tick_of_day: int) -> bool:
        """Whether this NPC is at home at *tick_of_day*."""
        return tick_of_day < _MORNING_COMMUTE_START or tick_of_day >= _EVENING_COMMUTE_END


# ── population generator ────────────────────────────────────────


@dataclass
class NpcPopulation:
    """Collection of NPCs with batch generation and query utilities."""

    npcs: list[NPC] = field(default_factory=list)

    @classmethod
    def generate(cls, city: City, scale: int | None = None) -> NpcPopulation:
        """Generate a population of NPCs based on city stations.

        NPC home stations are assigned from stations in the first half
        of the station list (proxy for "residential" zone), work stations
        from the second half (proxy for "commercial" zone).

        Args:
            city: The city model with stations.
            scale: Number of NPCs per station. Defaults to 100 if not
                specified, clamped to [50, 200].

        Returns:
            A new NpcPopulation with generated NPCs.
        """
        station_ids = list(city.stations.keys())
        if not station_ids:
            return cls()

        n_stations = len(station_ids)
        per_station = max(50, min(200, scale if scale is not None else 100))
        total = n_stations * per_station

        # Split stations into "residential" (first half) and "commercial" (second half)
        split = n_stations // 2
        if split < 1:
            split = 1  # at least 1 home zone
        home_pool = station_ids[:split]
        work_pool = station_ids[split:] if split < n_stations else station_ids

        npcs: list[NPC] = []
        rng = random.Random(42)  # deterministic seed for reproducibility
        for i in range(total):
            npcs.append(NPC(
                id=f"npc_{i:06d}",
                home_station=rng.choice(home_pool),
                work_station=rng.choice(work_pool),
            ))

        return cls(npcs=npcs)

    def get_commuters(
        self,
        tick_of_day: int,
        station_id: str,
        sample_frac: float = 0.3,
    ) -> list[NPC]:
        """Return NPCs who want to commute *from* *station_id* at *tick_of_day*.

        Morning: NPCs at home_station → work_station
        Evening: NPCs at work_station → home_station

        Args:
            tick_of_day: Current tick within the day (0-1439).
            station_id: The station to query from.
            sample_frac: Fraction of matching NPCs to return (prevents
                overwhelming the simulation). Default 0.3.

        Returns:
            List of NPCs that would start a trip from *station_id* now.
        """
        is_morning = _MORNING_COMMUTE_START <= tick_of_day < _MORNING_COMMUTE_END
        is_evening = _EVENING_COMMUTE_START <= tick_of_day < _EVENING_COMMUTE_END

        if not is_morning and not is_evening:
            return []

        candidates: list[NPC] = []
        for npc in self.npcs:
            if is_morning and npc.home_station == station_id:
                candidates.append(npc)
            elif is_evening and npc.work_station == station_id:
                candidates.append(npc)

        if not candidates:
            return []

        # Sample a fraction to avoid overwhelming the simulation
        k = max(1, int(len(candidates) * sample_frac))
        return random.sample(candidates, min(k, len(candidates)))

    @property
    def size(self) -> int:
        return len(self.npcs)
