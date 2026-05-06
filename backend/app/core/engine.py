"""Simulation engine — orchestrates tick-by-tick execution."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from app.core.city import City
from app.core.fleet import Fleet, FleetSnapshot
from app.core.scheduler import RebalanceStrategy
from app.core.weather import Environment, WeatherGenerator


class SimState(enum.Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class SimulationNotRunningError(RuntimeError):
    """Raised when an action requires the simulation to be RUNNING."""


@dataclass
class SimConfig:
    """Internal simulation parameters."""

    ticks_per_day: int = 1440
    speed_multiplier: int = 60
    rebalance_interval_ticks: int = 60


class SimulationEngine:
    """Core simulation loop — advances time and updates fleet state.

    Usage::

        engine = SimulationEngine(city, fleet, strategy)
        engine.start()
        snapshot = engine.advance(1440)   # simulate one day
        engine.pause()
        engine.stop()
    """

    def __init__(
        self,
        city: City,
        fleet: Fleet,
        rebalance_strategy: RebalanceStrategy,
        config: SimConfig | None = None,
    ) -> None:
        self.city = city
        self.fleet = fleet
        self.strategy = rebalance_strategy
        self.config = config or SimConfig()
        self._weather_gen = WeatherGenerator(seed=42)

        self.state: SimState = SimState.STOPPED
        self.tick: int = 0
        self._last_rebalance_tick: int = 0

    # ── lifecycle ──────────────────────────────────────────────────

    def start(self) -> None:
        """Start or resume the simulation."""
        if self.state == SimState.RUNNING:
            raise SimulationNotRunningError("Simulation is already running")
        self.state = SimState.RUNNING

    def pause(self) -> None:
        """Pause the simulation."""
        if self.state != SimState.RUNNING:
            raise SimulationNotRunningError("Simulation is not running")
        self.state = SimState.PAUSED

    def stop(self) -> None:
        """Stop the simulation and reset tick count."""
        self.state = SimState.STOPPED
        self.tick = 0

    # ── time travel ────────────────────────────────────────────────

    def advance(self, steps: int = 1) -> FleetSnapshot:
        """Advance the simulation by *steps* ticks.

        Returns the fleet snapshot *after* the last tick.

        Raises
        ------
        SimulationNotRunningError
            If the engine is not in RUNNING state.
        """
        if self.state != SimState.RUNNING:
            raise SimulationNotRunningError(
                f"Cannot advance when engine state is {self.state.value}"
            )

        for _ in range(steps):
            self._tick()
        return self.fleet.snapshot()

    # ── internal ticks ─────────────────────────────────────────────

    def _tick(self) -> None:
        """Execute a single simulation tick."""
        self.tick += 1
        env = self._weather_gen.generate(self.tick)

        # === stub: real trip generation will go here (Phase 2) ===
        _ = env

        # periodic rebalance analysis
        if (
            self.config.rebalance_interval_ticks > 0
            and (self.tick - self._last_rebalance_tick)
            >= self.config.rebalance_interval_ticks
        ):
            snap = self.fleet.snapshot()
            report = self.strategy.analyse(self.city, snap, self.tick)
            self._last_rebalance_tick = self.tick
            # stub: orders are logged but not yet dispatched
            _ = report

    # ── helpers ────────────────────────────────────────────────────

    def time_of_day(self) -> str:
        """Return the simulated time-of-day string, e.g. ``"07:30"``."""
        total_minutes = self.tick % self.config.ticks_per_day
        h, m = divmod(total_minutes, 60)
        return f"{h:02d}:{m:02d}"

    def current_environment(self) -> Environment:
        """Return the weather/environment for the current tick."""
        return self._weather_gen.generate(self.tick)
