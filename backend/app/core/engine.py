"""SimulationEngine — main loop orchestrating tick-by-tick simulation."""

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


class SimulationNotRunningError(RuntimeError):
    """Raised when an action requires the simulation to be RUNNING."""


@dataclass
class SimulationEngine:
    """Drives the simulation forward tick by tick."""

    city: City
    fleet: Fleet
    environment: Environment
    strategy: RebalanceStrategy

    state: SimState = SimState.STOPPED
    tick: int = 0
    ticks_per_day: int = 1440
    speed_multiplier: int = 60

    _accumulator: int = 0

    def start(self) -> None:
        self.state = SimState.RUNNING

    def pause(self) -> None:
        if self.state == SimState.STOPPED:
            raise SimulationNotRunningError("Cannot pause a stopped simulation")
        self.state = SimState.PAUSED

    def stop(self) -> None:
        self.state = SimState.STOPPED

    def advance(self, steps: int = 1) -> FleetSnapshot:
        """Advance simulation by *steps* ticks (only if RUNNING)."""
        if self.state != SimState.RUNNING:
            raise SimulationNotRunningError(
                f"Simulation is {self.state.name}, not RUNNING"
            )
        for _ in range(steps):
            self._tick()
        return self.fleet.snapshot()

    def _tick(self) -> None:
        """Execute one simulation tick."""
        self.tick += 1
        self.environment.tick()
        # TODO(phase-2): generate trips based on demand model
        # TODO(phase-2): execute rebalance orders periodically

    def time_of_day(self) -> str:
        """Return formatted simulation time HH:MM within a 24-hour day."""
        mod = self.tick % self.ticks_per_day
        h, m = divmod(mod, 60)
        return f"{h:02d}:{m:02d}"

    @property
    def day_number(self) -> int:
        return self.tick // self.ticks_per_day

    def rebalance(self) -> None:
        """Run the rebalance strategy and produce dispatch orders."""
        station_inv: dict[str, int] = {}
        station_cap: dict[str, int] = {}
        for sid, station in self.city.stations.items():
            station_inv[sid] = len(self.fleet.bikes_at_station(sid))
            station_cap[sid] = station.capacity

        report = self.strategy.analyse(station_inv, station_cap)
        # TODO(phase-3): execute orders against a dispatch queue
        _ = report  # placeholder
