"""NPC Commute Model — home/work assignment, daily schedule, population generation.

Phase D (v0.4): Each NPC has a daily cycle with commute trips between home
and work stations, plus off-peak leisure/errand trips.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.city import Station


# ── Time-of-day schedule constants ──────────────────────────────

LOCATION_HOME = "home"
LOCATION_WORK = "work"
LOCATION_LEISURE = "leisure"


@dataclass(frozen=True)
class NPC:
    """A single non-player character with a daily commute pattern.

    ``schedule`` maps tick-of-day → location tag:
    - 0-359 (00:00-05:59): home
    - 360-479 (06:00-07:59): morning commute → work
    - 480-1019 (08:00-16:59): at work
    - 1020-1139 (17:00-18:59): evening commute → home
    - 1140-1439 (19:00-23:59): at home (or leisure)
    """

    id: str
    home_station: str
    work_station: str
    schedule: dict[int, str] = field(default_factory=dict, compare=False)

    def location_at(self, tick: int) -> str:
        """Return the location tag for the given tick of day."""
        tick_of_day = tick % 1440
        # Find the latest schedule entry ≤ tick_of_day
        best_key = -1
        best_val = LOCATION_HOME
        for k, v in self.schedule.items():
            if k <= tick_of_day and k >= best_key:
                best_key = k
                best_val = v
        return best_val

    def is_commuting(self, tick: int) -> bool:
        """Return True if this NPC is in transition during this tick."""
        tick_of_day = tick % 1440
        # Morning commute: 360-479 (06:00-07:59)
        # Evening commute: 1020-1139 (17:00-18:59)
        return (360 <= tick_of_day < 480) or (1020 <= tick_of_day < 1140)

    def trip_od(
        self, tick: int, stations: dict[str, Station]
    ) -> tuple[str | None, str | None]:
        """Return (from_station, to_station) if this NPC generates a trip at *tick*.

        Returns (None, None) if no trip is generated at this tick.
        """
        tick_of_day = tick % 1440

        # Morning commute: go from home to work
        if tick_of_day == 360:  # 06:00 — depart for work
            return (self.home_station, self.work_station)

        # Evening commute: go from work to home
        if tick_of_day == 1020:  # 17:00 — depart for home
            return (self.work_station, self.home_station)

        return (None, None)


def _build_default_schedule() -> dict[int, str]:
    """Build the default daily schedule for an NPC.

    Returns dict mapping tick_of_day → location_tag.
    """
    return {
        0: LOCATION_HOME,      # 00:00 — asleep
        360: LOCATION_WORK,    # 06:00 — morning commute starts
        480: LOCATION_WORK,    # 08:00 — at work
        1020: LOCATION_HOME,   # 17:00 — evening commute starts
        1140: LOCATION_HOME,   # 19:00 — at home
    }


@dataclass
class NpcPopulation:
    """Collection of NPCs with commute-aware query methods.

    Use ``NpcPopulation.generate(stations)`` classmethod to create a
    population for a given city.
    """

    npcs: list[NPC] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.npcs)

    def __getitem__(self, index: int) -> NPC:
        return self.npcs[index]

    def get_npcs_at_station(self, station_id: str) -> list[NPC]:
        """Return all NPCs that have this station as home or work."""
        return [
            n for n in self.npcs
            if n.home_station == station_id or n.work_station == station_id
        ]

    def get_commuters_between(
        self, from_station: str, to_station: str
    ) -> list[NPC]:
        """Return all NPCs that commute between these two stations."""
        return [
            n for n in self.npcs
            if n.home_station == from_station and n.work_station == to_station
        ]

    @classmethod
    def generate(
        cls,
        stations: dict[str, Station],
        *,
        n_npcs: int | None = None,
        seed: int = 42,
    ) -> NpcPopulation:
        """Generate an NPC population for the given stations.

        Each NPC is assigned a random home station and a random (different)
        work station. NPC count scales with city size: default is
        ``n_stations * 50``, clamped to [50, 5000].

        Args:
            stations: City stations dict.
            n_npcs: Override NPC count (auto-calculated if None).
            seed: Random seed for reproducibility.

        Returns:
            A new NpcPopulation instance.
        """
        if not stations:
            return cls()

        station_ids = list(stations.keys())
        if n_npcs is None:
            n_npcs = min(max(len(station_ids) * 50, 50), 5000)

        rng = random.Random(seed)
        schedule = _build_default_schedule()
        npcs: list[NPC] = []

        for i in range(n_npcs):
            home = rng.choice(station_ids)
            work = rng.choice([s for s in station_ids if s != home]) if len(station_ids) > 1 else home
            npcs.append(
                NPC(
                    id=f"npc_{i:05d}",
                    home_station=home,
                    work_station=work,
                    schedule=schedule,
                )
            )

        return cls(npcs=npcs)
