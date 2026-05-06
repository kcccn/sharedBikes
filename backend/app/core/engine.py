"""Simulation engine — main loop driving ticks, state machine, and time."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from app.core.fleet import Fleet, FleetSnapshot
from app.core.scheduler import GreedyThresholdStrategy, RebalanceStrategy
from app.core.weather import Environment


class SimState(Enum):
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()


class SimulationNotRunningError(RuntimeError):
    """Raised when an action requires the simulation to be RUNNING."""


@dataclass
class SimulationEngine:
    """Core simulation loop. Manages tick progression, fleet, weather, and
    periodic rebalancing."""

    fleet: Fleet = field(default_factory=Fleet)
    environment: Environment = field(default_factory=Environment)
    rebalancer: RebalanceStrategy = field(
        default_factory=GreedyThresholdStrategy
    )

    state: SimState = SimState.STOPPED
    tick: int = 0
    ticks_per_day: int = 1440
    speed_multiplier: int = 60
    rebalance_interval_ticks: int = 60

    # ── lifecycle ────────────────────────────────────────────────────

    def start(self) -> None:
        if self.state == SimState.RUNNING:
            return  # idempotent
        self.state = SimState.RUNNING

    def pause(self) -> None:
        if self.state != SimState.RUNNING:
            return  # only meaningful from RUNNING
        self.state = SimState.PAUSED

    def stop(self) -> None:
        self.state = SimState.STOPPED

    # ── main loop ────────────────────────────────────────────────────

    def advance(self, steps: int = 1) -> FleetSnapshot:
        """Advance the simulation by *steps* ticks. Returns the final
        fleet snapshot. Raises SimulationNotRunningError if not RUNNING."""
        if self.state != SimState.RUNNING:
            raise SimulationNotRunningError(
                f"Cannot advance: engine is {self.state.name}"
            )
        for _ in range(steps):
            self._tick()
        return self.fleet.snapshot()

    def _tick(self) -> None:
        """Execute one simulation tick."""
        self.tick += 1

        # Periodic rebalancing
        if self.tick % self.rebalance_interval_ticks == 0:
            self._run_rebalance()

    def _run_rebalance(self) -> None:
        """Evaluate fleet balance and execute rebalancing orders."""
        report = self.rebalancer.analyse(
            inventory=self.fleet.station_inventory,
            capacities=self.fleet._station_capacity,
        )
        for order in report.suggested_orders:
            for _ in range(order.count):
                try:
                    self.fleet.undock_bike(
                        _pick_bike_at_station(self.fleet, order.from_station_id)
                    )
                except (ValueError, KeyError):
                    break  # no more bikes at that station

    # ── time helpers ─────────────────────────────────────────────────

    def time_of_day(self) -> str:
        """Return the simulated time-of-day string (HH:MM) for the current
        tick, respecting ticks_per_day."""
        total_minutes = self.tick % self.ticks_per_day
        h, m = divmod(total_minutes, 60)
        return f"{h:02d}:{m:02d}"

    def day_number(self) -> int:
        return self.tick // self.ticks_per_day + 1


def _pick_bike_at_station(fleet: Fleet, station_id: str) -> str:
    """Return the bike_id of any docked bike at the given station."""
    for bid, bike in fleet.bikes.items():
        if bike.current_station_id == station_id and bike.state.name == "DOCKED":
            return bid
    raise ValueError(f"No docked bikes at station {station_id}")
