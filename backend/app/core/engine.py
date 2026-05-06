"""Simulation engine — the main loop driving the world forward."""

from __future__ import annotations

import enum

from app.core.city import City
from app.core.config import SimulationConfig
from app.core.fleet import Fleet, FleetSnapshot
from app.core.scheduler import RebalanceStrategy
from app.core.weather import Environment, WeatherGenerator


class SimState(enum.Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class SimulationNotRunningError(RuntimeError):
    """Raised when an action requires a RUNNING state."""


class SimulationEngine:
    """Core simulation loop. Tick-driven, deterministic."""

    def __init__(
        self,
        city: City,
        fleet: Fleet,
        config: SimulationConfig | None = None,
        weather_gen: WeatherGenerator | None = None,
        rebalance_strategy: RebalanceStrategy | None = None,
    ) -> None:
        self._city = city
        self._fleet = fleet
        self._config = config or SimulationConfig()
        self._weather_gen = weather_gen or WeatherGenerator()
        self._rebalance_strategy = rebalance_strategy

        self._tick: int = 0
        self._state: SimState = SimState.STOPPED
        self._environment: Environment = Environment()

    # ---- state control ----

    def start(self) -> None:
        if self._state == SimState.RUNNING:
            return
        self._state = SimState.RUNNING

    def pause(self) -> None:
        if self._state != SimState.RUNNING:
            raise SimulationNotRunningError("Cannot pause when not running")
        self._state = SimState.PAUSED

    def resume(self) -> None:
        if self._state != SimState.PAUSED:
            raise SimulationNotRunningError("Cannot resume when not paused")
        self._state = SimState.RUNNING

    def stop(self) -> None:
        self._state = SimState.STOPPED

    # ---- tick mechanics ----

    def advance(self, steps: int = 1) -> FleetSnapshot:
        """Advance the simulation by *steps* ticks. Raises if not RUNNING."""
        if self._state != SimState.RUNNING:
            raise SimulationNotRunningError(
                f"Cannot advance when state is {self._state.value}"
            )
        for _ in range(steps):
            self._tick()
        return self._fleet.snapshot()

    def _tick(self) -> None:
        """Execute a single simulation tick."""
        self._environment = self._weather_gen.generate(self._tick)
        self._tick += 1

    # ---- properties ----

    @property
    def tick(self) -> int:
        return self._tick

    @property
    def state(self) -> SimState:
        return self._state

    @property
    def environment(self) -> Environment:
        return self._environment

    @property
    def fleet(self) -> Fleet:
        return self._fleet

    @property
    def city(self) -> City:
        return self._city

    def time_of_day(self) -> str:
        """Return simulated time-of-day string (HH:MM)."""
        total_minutes = self._tick % self._config.ticks_per_day
        h, m = divmod(total_minutes, 60)
        return f"{h:02d}:{m:02d}"
