"""Simulation engine main loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.core.city import City
from app.core.fleet import Fleet, FleetSnapshot
from app.core.scheduler import RebalanceStrategy
from app.core.weather import Environment


class SimState(Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class SimulationEngine:
    """Orchestrates the simulation tick loop."""

    city: City
    fleet: Fleet = field(default_factory=Fleet)
    environment: Environment = field(default_factory=Environment)
    strategy: RebalanceStrategy | None = None
    state: SimState = SimState.CREATED
    tick: int = 0

    # --- Life-cycle ---

    def start(self) -> None:
        if self.state == SimState.CREATED:
            self.environment.randomize()
        self.state = SimState.RUNNING

    def pause(self) -> None:
        if self.state == SimState.RUNNING:
            self.state = SimState.PAUSED

    def resume(self) -> None:
        if self.state == SimState.PAUSED:
            self.state = SimState.RUNNING

    def stop(self) -> None:
        self.state = SimState.STOPPED

    def reset(self) -> None:
        self.fleet = Fleet()
        self.environment = Environment()
        self.tick = 0
        self.state = SimState.CREATED

    # --- Tick ---

    def advance(self, steps: int = 1) -> FleetSnapshot | None:
        """Execute *steps* ticks and return the final snapshot.

        Returns ``None`` when the engine is not running.
        """
        if self.state != SimState.RUNNING:
            return None
        for _ in range(steps):
            self._tick()
        return self.fleet.snapshot()

    def _tick(self) -> None:
        self.tick += 1
        # Weather refresh
        if self.tick % 60 == 0:
            self.environment.randomize()
        self.environment.tick()
        # Rebalancing (periodic)
        if self.strategy and self.tick % 120 == 0:
            report = self.strategy.analyse(self.city.stations, self.fleet.snapshot())
            for order in report.suggested_orders:
                self._apply_order(order)

    def _apply_order(self, order) -> None:
        # simplistic: move bikes from overflow to starving station
        from_inv = sum(
            1
            for b in self.fleet.bikes.values()
            if b.status.value == "docked" and b.station_id == order.from_station_id
        )
        to_move = min(order.bike_count, from_inv)
        moved = 0
        for bike in list(self.fleet.bikes.values()):
            if moved >= to_move:
                break
            if bike.status.value == "docked" and bike.station_id == order.from_station_id:
                self.fleet.dock_bike(bike.bike_id, order.to_station_id)
                moved += 1

    # --- Queries ---

    def time_of_day(self) -> str:
        """Simulation time as HH:MM string (24h, ignoring speed multiplier)."""
        total_minutes = self.tick % 1440
        h, m = divmod(total_minutes, 60)
        return f"{h:02d}:{m:02d}"

    def sim_day(self) -> int:
        return self.tick // 1440
