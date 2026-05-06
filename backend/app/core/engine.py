"""Simulation engine — the main tick loop that drives the simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from app.core.city import City
from app.core.fleet import Fleet, FleetSnapshot
from app.core.scheduler import RebalanceStrategy
from app.core.weather import Environment


class SimState(Enum):
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()


class SimulationNotRunningError(Exception):
    """Raised when an action requires the engine to be RUNNING."""


@dataclass
class SimulationEngine:
    """The central simulation driver — ticks forward simulation time."""

    city: City
    fleet: Fleet = field(default_factory=Fleet)
    environment: Environment = field(default_factory=Environment)
    config: dict | None = None

    tick: int = 0
    state: SimState = SimState.STOPPED
    ticks_per_day: int = 1440
    speed_multiplier: int = 60
    rebalance_strategy: RebalanceStrategy | None = None

    def start(self) -> None:
        """Start (or resume) the simulation."""
        if self.state == SimState.STOPPED:
            # Initialise fleet from city stations on first start
            pass  # TODO(phase-1): deploy initial bikes
        self.state = SimState.RUNNING

    def pause(self) -> None:
        """Pause the simulation."""
        if self.state != SimState.RUNNING:
            raise SimulationNotRunningError("Engine is not running")
        self.state = SimState.PAUSED

    def stop(self) -> None:
        """Stop the simulation and reset state."""
        self.state = SimState.STOPPED
        self.tick = 0

    def advance(self, steps: int = 1) -> FleetSnapshot:
        """Advance forward *steps* ticks.  Raises if engine is not RUNNING."""
        if self.state != SimState.RUNNING:
            raise SimulationNotRunningError(
                "Cannot advance — engine is not RUNNING"
            )
        for _ in range(steps):
            self._tick()
        return self.fleet.snapshot()

    def time_of_day(self) -> str:
        """Return the current simulated time as 'HH:MM'."""
        total_minutes = (self.tick % self.ticks_per_day) // self.speed_multiplier
        h, m = divmod(total_minutes, 60)
        return f"{h:02d}:{m:02d}"

    def _tick(self) -> None:
        """Execute one simulation tick."""
        self.tick += 1

        # TODO(phase-2): NPC trip generation
        # TODO(phase-2): weather updates
        # TODO(phase-2): periodic rebalancing
