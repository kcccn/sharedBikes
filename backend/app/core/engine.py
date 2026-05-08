"""SimulationEngine — main loop orchestrating tick-by-tick simulation.

Phase 2 integrates the Ledger-First economic system:
- ``TripExecutor`` manages trip lifecycle (bike assignment + completion)
- ``CostEngine`` computes fixed costs per tick
- ``PricingEngine`` computes revenue for completed trips
- ``Ledger`` stores all financial entries (immutable, chunked)
- ``DailyReport`` is generated at each day boundary
- ``SimState.BANKRUPT`` terminates the simulation if losses exceed threshold
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Callable

from app.core.city import City
from app.core.costing import CostEngine
from app.core.fleet import Fleet, FleetSnapshot
from app.core.scheduler import RebalanceStrategy
from app.core.weather import Environment

if TYPE_CHECKING:
    from app.core.finance import LedgerEntry
    from app.core.pricing import PricingTier
    from app.core.trip_executor import ActiveTrip, TripExecutor
    from app.services.demand_service import TripGenerator, TripRequest


class SimState(Enum):
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()
    BANKRUPT = auto()  # added in Phase 2 — losses exceeded threshold


class SimulationNotRunningError(RuntimeError):
    """Raised when an action requires the simulation to be RUNNING."""


# ── daily report ────────────────────────────────────────────────


@dataclass(frozen=True)
class DailyReport:
    """Summary report generated at the end of each simulation day."""

    day: int
    final_tick: int
    revenue_today: float
    costs_today: float
    profit_today: float
    cumulative_balance: float
    active_trips: int
    alert: str = ""


# ── tick events ─────────────────────────────────────────────────


@dataclass
class TickEvents:
    """Immutable record of everything that happened during one tick.

    Event-sourced pattern: each tick produces a self-contained event object
    that can be replayed, inspected, or streamed to clients.

    ``revenue`` and ``costs`` are now derived properties from ``ledger_entries``,
    maintaining backward compatibility with existing consumers.
    """

    tick: int
    time_of_day: str
    trips: list[TripRequest] = field(default_factory=list)
    ledger_entries: list[LedgerEntry] = field(default_factory=list)
    weather: str = "CLEAR"
    station_inventory: dict[str, int] = field(default_factory=dict)

    @property
    def revenue(self) -> float:
        return sum(e.amount for e in self.ledger_entries if e.amount > 0)

    @property
    def costs(self) -> float:
        return abs(sum(e.amount for e in self.ledger_entries if e.amount < 0))


# ── engine ──────────────────────────────────────────────────────


@dataclass
class SimulationEngine:
    """Drives the simulation forward tick by tick."""

    city: City
    fleet: Fleet
    environment: Environment
    strategy: RebalanceStrategy
    trip_generator: TripGenerator | None = None

    # Phase 2: economic system components
    pricing_tier: object | None = None  # PricingTier — resolved in start()
    cost_engine: CostEngine | None = None
    trip_executor: TripExecutor | None = None
    bankruptcy_threshold: float = -5000.0  # balance below this → BANKRUPT

    state: SimState = SimState.STOPPED
    tick: int = 0
    ticks_per_day: int = 1440
    speed_multiplier: int = 60

    _accumulator: int = 0
    _events_history: list[TickEvents] = field(default_factory=list)

    # Phase 2: immutable ledger (never cleared)
    _ledger: object | None = None  # Ledger — lazily initialised
    _daily_reports: list[DailyReport] = field(default_factory=list)

    # ── lifecycle ────────────────────────────────────────────────

    def start(self) -> None:
        # Lazy-import to avoid circular import at module level
        from app.core.finance import Ledger
        from app.core.pricing import STANDARD
        from app.core.trip_executor import TripExecutor

        if self._ledger is None:
            self._ledger = Ledger()
        if self.pricing_tier is None:
            self.pricing_tier = STANDARD
        if self.trip_executor is None:
            self.trip_executor = TripExecutor(fleet=self.fleet)
        if self.cost_engine is None:
            self.cost_engine = CostEngine()

        self.state = SimState.RUNNING

    def pause(self) -> None:
        if self.state == SimState.STOPPED:
            raise SimulationNotRunningError("Cannot pause a stopped simulation")
        self.state = SimState.PAUSED

    def stop(self) -> None:
        self.state = SimState.STOPPED

    def advance(self, steps: int = 1) -> FleetSnapshot:
        """Advance simulation by *steps* ticks (only if RUNNING)."""
        if self.state not in (SimState.RUNNING, SimState.BANKRUPT):
            raise SimulationNotRunningError(
                f"Simulation is {self.state.name}, not RUNNING"
            )
        if self.state == SimState.BANKRUPT:
            # Bankrupt simulation doesn't progress — return last snapshot
            return self.fleet.snapshot()

        for _ in range(steps):
            events = self._tick()
            self._events_history.append(events)
        return self.fleet.snapshot()

    @property
    def recent_events(self) -> list[TickEvents]:
        """Return all tick events collected so far."""
        return list(self._events_history)

    def clear_events(self) -> None:
        """Clear the event history buffer.

        Note: this does NOT clear the ledger. The ledger is the permanent
        financial record and is never cleared.
        """
        self._events_history.clear()

    # ── Phase 2: public ledger access ────────────────────────────

    @property
    def ledger(self) -> object:
        """Return the immutable ledger (lazily initialised)."""
        from app.core.finance import Ledger

        if self._ledger is None:
            self._ledger = Ledger()
        return self._ledger

    @property
    def daily_reports(self) -> list[DailyReport]:
        """Return all daily reports generated so far."""
        return list(self._daily_reports)

    @property
    def balance(self) -> float:
        """Current ledger balance (convenience)."""
        return self.ledger.balance()  # type: ignore[union-attr]

    @property
    def is_bankrupt(self) -> bool:
        """Whether the simulation has hit bankruptcy threshold."""
        return self.state == SimState.BANKRUPT

    # ── _tick — the core pipeline ────────────────────────────────

    def _tick(self) -> TickEvents:
        """Execute one simulation tick and return the events that occurred.

        Pipeline order (Architect's specification: costs before revenue):
        1. Advance time + environment
        2. Generate trip demand
        3. TripExecutor: assign bikes + complete trips
        4. CostEngine: compute fixed/variable costs
        5. PricingEngine: compute revenue for completed trips
        6. Ledger.append(all entries)
        7. Check bankruptcy condition
        8. Generate DailyReport at day boundary
        9. Return TickEvents
        """
        self.tick += 1
        self.environment.tick()

        tick_in_day = self.tick % self.ticks_per_day

        # ── 1. Generate trip demand ──────────────────────────────
        trips: list[TripRequest] = []
        if self.trip_generator is not None:
            trips = self.trip_generator.generate(self.tick, self.city.stations)

        # Validate station IDs
        valid_trips: list[TripRequest] = []
        for trip in trips:
            if trip.from_station in self.city.stations and trip.to_station in self.city.stations:
                valid_trips.append(trip)
        trips = valid_trips

        # ── 2. Execute trips (bike assignment + completion) ──────
        executor = self.trip_executor
        completed_trips: list[ActiveTrip] = []
        if executor is not None:
            # Build distance cache for this tick's trips
            distances: dict[tuple[str, str], float] = {}
            for trip in trips:
                key = (trip.from_station, trip.to_station)
                if key not in distances:
                    d = self.city.shortest_path_distance(trip.from_station, trip.to_station)
                    distances[key] = d if d is not None else 2.0  # fallback

            completed_trips = executor.advance(self.tick, trips, distances)

        # ── 3. Compute costs (fixed costs on first tick of day) ──
        ledger_entries: list[LedgerEntry] = []
        if self.cost_engine is not None:
            cost_entries = self.cost_engine.per_tick(
                tick=self.tick,
                tick_in_day=tick_in_day,
                total_bikes=len(self.fleet.bikes),
                total_stations=len(self.city.stations),
            )
            ledger_entries.extend(cost_entries)

        # ── 4. Compute revenue for completed trips ───────────────
        from app.core.pricing import PricingEngine

        pricing = PricingEngine()
        tier = self.pricing_tier
        for at in completed_trips:
            entry = pricing.apply(
                trip_id=at.trip_id,
                distance_km=at.distance_km,
                tier=tier,
                tick=self.tick,
            )
            ledger_entries.append(entry)

        # ── 5. Append to ledger ──────────────────────────────────
        if ledger_entries:
            self._ledger = self._ledger.append(ledger_entries)  # type: ignore[union-attr]

        # ── 6. Check bankruptcy ──────────────────────────────────
        if self.balance < self.bankruptcy_threshold:
            self.state = SimState.BANKRUPT

        # ── 7. Snapshot station inventory ────────────────────────
        station_inventory: dict[str, int] = {}
        for sid in self.city.stations:
            station_inventory[sid] = len(self.fleet.bikes_at_station(sid))

        # ── 8. Generate DailyReport at day boundary ──────────────
        report: DailyReport | None = None
        if tick_in_day == 0 and self.tick > 0:
            day = self.day_number
            tick_from = (day - 1) * self.ticks_per_day
            tick_to = self.tick

            alert = ""
            if self.balance < self.bankruptcy_threshold * 0.5:
                alert = (
                    f"⚠️ 预警：余额 ¥{self.balance:.2f}，"
                    f"若持续亏损将进入破产程序（阈值 ¥{self.bankruptcy_threshold:.0f}）"
                )
            elif self.balance < 0:
                alert = f"⚠️ 当前亏损 ¥{abs(self.balance):.2f}，请关注营收状况"

            today_revenue = self.ledger.revenue_total(tick_from, tick_to)  # type: ignore[union-attr]
            today_costs = self.ledger.cost_total(tick_from, tick_to)  # type: ignore[union-attr]

            report = DailyReport(
                day=day,
                final_tick=self.tick,
                revenue_today=today_revenue,
                costs_today=today_costs,
                profit_today=today_revenue - today_costs,
                cumulative_balance=self.balance,
                active_trips=executor.active_trip_count if executor else 0,
                alert=alert,
            )
            self._daily_reports.append(report)

        # ── 9. Return TickEvents ─────────────────────────────────
        events = TickEvents(
            tick=self.tick,
            time_of_day=self.time_of_day(),
            trips=trips,
            ledger_entries=ledger_entries,
            weather=self.environment.condition.name,
            station_inventory=station_inventory,
        )

        return events

    # ── utilities ────────────────────────────────────────────────

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
