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


class SimulationNotRunningError(RuntimeError):
    """Raised when an operation requires the simulation to be RUNNING."""


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
    ticks_per_day: int = 1440  # Aligned with SimulationConfig.ticks_per_day

    # ── Lifecycle ─────────────────────────────────────────

    def start(self) -> None:
        if self.state == SimState.RUNNING:
            raise RuntimeError("Simulation is already running")
        self.state = SimState.RUNNING

    def pause(self) -> None:
        if self.state != SimState.RUNNING:
            raise RuntimeError("Can only pause a running simulation")
        self.state = SimState.PAUSED

    def stop(self) -> None:
        self.state = SimState.STOPPED

    # ── Tick ──────────────────────────────────────────────

    def advance(self, steps: int = 1) -> FleetSnapshot:
        """
        Advance simulation by *steps* ticks (or one tick if omitted).

        Returns a FleetSnapshot for external consumers (API, viz).

        Raises ``SimulationNotRunningError`` if the engine is not RUNNING.
        """
        if self.state != SimState.RUNNING:
            raise SimulationNotRunningError(
                f"Cannot advance — simulation is {self.state.value}"
            )
        for _ in range(steps):
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
        total_minutes = self.tick % self.ticks_per_day
        h, m = divmod(total_minutes, 60)
        return f"{h:02d}:{m:02d}"

    def day_number(self) -> int:
        return self.tick // self.ticks_per_day + 1
