"""Simulation engine — main loop."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable

from app.config import SimulationConfig
from app.core.city import City
from app.core.fleet import Bike, BikeStatus, Fleet, FleetSnapshot
from app.core.scheduler import GreedyThresholdStrategy, RebalanceStrategy
from app.core.weather import Environment


class SimState(Enum):
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()


class SimulationNotRunningError(RuntimeError):
    """Raised when an action requires the simulation to be running."""


@dataclass
class SimulationEngine:
    """Core simulation loop — orchestrates ticks, fleet, city, and environment.

    Usage::

        engine = SimulationEngine(city, fleet, env, config)
        engine.start()
        engine.advance(1440)   # simulate one day
        snap = engine.fleet_snapshot()
    """

    city: City
    fleet: Fleet
    env: Environment
    config: SimulationConfig
    rebalancer: RebalanceStrategy = GreedyThresholdStrategy()

    tick: int = 0
    state: SimState = SimState.STOPPED

    # Optional callbacks for side‑effects (logging, events, etc.)
    on_tick: Callable[[int], None] | None = None
    on_rebalance: Callable[[list], None] | None = None

    # ── lifecycle ────────────────────────────────────────

    def start(self) -> None:
        if self.state == SimState.RUNNING:
            raise SimulationNotRunningError("Simulation is already running")
        self.state = SimState.RUNNING

    def pause(self) -> None:
        if self.state != SimState.RUNNING:
            raise SimulationNotRunningError("Simulation is not running")
        self.state = SimState.PAUSED

    def resume(self) -> None:
        if self.state != SimState.PAUSED:
            raise SimulationNotRunningError("Simulation is not paused")
        self.state = SimState.RUNNING

    def stop(self) -> None:
        self.state = SimState.STOPPED

    def reset(self) -> None:
        """Reset engine to initial state (fleet is not cleared)."""
        self.tick = 0
        self.state = SimState.STOPPED

    # ── tick logic ───────────────────────────────────────

    def advance(self, steps: int = 1) -> FleetSnapshot:
        """Run *steps* ticks of simulation.

        Returns the fleet snapshot after all ticks.
        Raises *SimulationNotRunningError* if the engine is not RUNNING.
        """
        if self.state != SimState.RUNNING:
            raise SimulationNotRunningError(
                f"Cannot advance — engine is {self.state.name}"
            )
        for _ in range(steps):
            self._tick()
            self.tick += 1
            if self.on_tick:
                self.on_tick(self.tick)
        return self.fleet.snapshot()

    def _tick(self) -> None:
        """Execute one simulation tick."""
        self._update_environment()
        self._process_trips()
        self._maybe_rebalance()

    def _update_environment(self) -> None:
        self.env.tick_events()
        minutes = self.tick % self.config.ticks_per_day
        h, m = divmod(minutes, 60)
        self.env.time_of_day = f"{h:02d}:{m:02d}"

    def _process_trips(self) -> None:
        """Placeholder: NPC trip generation (Phase 2)."""
        # TODO(phase-2): generate trips based on demand model

    def _maybe_rebalance(self) -> None:
        """Run rebalancing logic at configured intervals."""
        if self.tick % self.config.rebalance_interval_ticks != 0:
            return
        report = self.rebalancer.analyse(
            station_counts=self._station_counts(),
            station_capacities=self._station_capacities(),
            starvation_threshold=self.config.starvation_threshold,
            overflow_threshold=self.config.overflow_threshold,
        )
        if self.on_rebalance and report.suggested_orders:
            self.on_rebalance(report.suggested_orders)

    # ── helpers ──────────────────────────────────────────

    def _station_counts(self) -> dict[str, int]:
        return {
            sid: self.fleet.count_docked(sid)
            for sid in self.city.stations
        }

    def _station_capacities(self) -> dict[str, int]:
        return {
            sid: station.capacity
            for sid, station in self.city.stations.items()
        }

    def fleet_snapshot(self) -> FleetSnapshot:
        return self.fleet.snapshot()
