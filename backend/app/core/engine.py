"""Main simulation loop — orchestrates tick-level updates across all sub-systems."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.core.city import City
from app.core.fleet import Fleet, FleetSnapshot
from app.core.weather import Environment


class SimState(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


@dataclass
class SimulationEngine:
    """
    Heart of the game loop.

    **Owns** the mutable simulation state: city, fleet, environment.
    The API layer reads snapshots; mutation only happens here.
    """

    city: City
    fleet: Fleet = field(default_factory=Fleet)
    environment: Environment = field(default_factory=Environment)

    tick: int = 0
    state: SimState = SimState.STOPPED

    # ── Lifecycle ─────────────────────────────────────────

    def start(self) -> None:
        self.state = SimState.RUNNING

    def pause(self) -> None:
        self.state = SimState.PAUSED

    def stop(self) -> None:
        self.state = SimState.STOPPED

    # ── Tick ──────────────────────────────────────────────

    def advance(self, steps: int = 1) -> FleetSnapshot:
        """
        Advance simulation by *steps* ticks (or one tick if omitted).

        Returns a FleetSnapshot for external consumers (API, viz).
        """
        for _ in range(steps):
            if self.state != SimState.RUNNING:
                break
            self._tick()
        return self.fleet.snapshot()

    def _tick(self) -> None:
        """Execute a single simulation tick."""

        # 1. Environment changes
        self.environment.tick()

        # 2. Demand generation (NPC trip requests)
        # TODO(phase-2): self._generate_trip_requests()

        # 3. Process active trips
        # TODO(phase-2): self._complete_arriving_trips()

        # 4. Rebalancing triggers
        # TODO(phase-2): self._check_rebalance_triggers()

        self.tick += 1

    # ── Queries ───────────────────────────────────────────

    def time_of_day(self) -> str:
        """Return a human-readable clock string based on current tick."""
        total_minutes = self.tick % 1440  # 1440 ticks = 1 day
        h, m = divmod(total_minutes, 60)
        return f"{h:02d}:{m:02d}"

    def day_number(self) -> int:
        return self.tick // 1440 + 1
