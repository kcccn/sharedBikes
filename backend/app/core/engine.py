"""SimulationEngine — main loop orchestrating tick-by-tick simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

from app.core.city import City
from app.core.fleet import Fleet, FleetSnapshot
from app.core.scheduler import RebalanceStrategy
from app.core.weather import Environment

if TYPE_CHECKING:
    from app.services.demand_service import TripGenerator, TripRequest


class SimState(Enum):
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()


class SimulationNotRunningError(RuntimeError):
    """Raised when an action requires the simulation to be RUNNING."""


@dataclass
class TickEvents:
    """Immutable record of everything that happened during one tick.

    Event-sourced pattern: each tick produces a self-contained event object
    that can be replayed, inspected, or streamed to clients.
    """

    tick: int
    time_of_day: str
    trips: list[TripRequest] = field(default_factory=list)
    revenue: float = 0.0
    costs: float = 0.0
    weather: str = "CLEAR"
    station_inventory: dict[str, int] = field(default_factory=dict)


@dataclass
class SimulationEngine:
    """Drives the simulation forward tick by tick."""

    city: City
    fleet: Fleet
    environment: Environment
    strategy: RebalanceStrategy
    trip_generator: TripGenerator | None = None

    state: SimState = SimState.STOPPED
    tick: int = 0
    ticks_per_day: int = 1440
    speed_multiplier: int = 60

    _accumulator: int = 0
    _events_history: list[TickEvents] = field(default_factory=list)

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
            events = self._tick()
            self._events_history.append(events)
        return self.fleet.snapshot()

    @property
    def recent_events(self) -> list[TickEvents]:
        """Return all tick events collected so far."""
        return list(self._events_history)

    def clear_events(self) -> None:
        """Clear the event history (e.g. after a full day's analysis)."""
        self._events_history.clear()

    def _tick(self) -> TickEvents:
        """Execute one simulation tick and return the events that occurred."""
        self.tick += 1
        self.environment.tick()

        # Generate trip demand
        trips: list[TripRequest] = []
        if self.trip_generator is not None:
            trips = self.trip_generator.generate(self.tick, self.city.stations)

        # TripRequest station-ID guard — skip invalid trips
        valid_trips: list[TripRequest] = []
        for trip in trips:
            if trip.from_station in self.city.stations and trip.to_station in self.city.stations:
                valid_trips.append(trip)
        trips = valid_trips

        # TODO(phase-2): execute trips (dock/undock bikes, compute revenue)
        # TODO(phase-2): execute rebalance orders periodically

        # Snapshot station inventory
        station_inventory: dict[str, int] = {}
        for sid in self.city.stations:
            station_inventory[sid] = len(self.fleet.bikes_at_station(sid))

        return TickEvents(
            tick=self.tick,
            time_of_day=self.time_of_day(),
            trips=trips,
            revenue=0.0,
            costs=0.0,
            weather=self.environment.condition.name,
            station_inventory=station_inventory,
        )

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
