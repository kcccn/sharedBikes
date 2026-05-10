"""Achievement engine — DSL, tick-driven evaluation, and Ledger integration.

Phase 6 P0: Pure backend module with zero UI dependency.
AchievementEngine subscribes to ``EventBus`` ``"tick"`` events as a sibling
consumer alongside the WebSocket broadcaster.

Architecture
------------
::

    EventBus.publish("tick", TickEvents)
             │
             ▼
    ┌─────────────────────────────────┐
    │  AchievementEngine              │
    │  ├─ registry: dict[str, ...]    │
    │  ├─ state: AchievementState     │
    │  └─ evaluate(TickEvents)        │
    └────────┬────────────────────────┘
             │ unlock → Ledger.append(...)
             ▼
    ┌─────────────────────────────────┐
    │  Ledger (immutable, append-only)│
    │  RevenueCategory.ACHIEVEMENT    │
    └─────────────────────────────────┘
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Protocol

from app.core.event_bus import EventBus
from app.core.finance import Ledger, LedgerEntry, RevenueCategory


# ── enums ───────────────────────────────────────────────────────


class AchievementCategory(Enum):
    """Classification of achievement types."""

    MILESTONE = auto()  # One-time threshold unlock
    STREAK = auto()  # Consecutive period(s) meeting condition
    PERIODIC = auto()  # Daily / weekly evaluation


class AchievementUnlockState(Enum):
    """Runtime unlock state of a single achievement."""

    LOCKED = auto()
    UNLOCKED = auto()
    HIDDEN = auto()  # Secret — not visible until unlocked


# ── core data-classes ───────────────────────────────────────────


@dataclass(frozen=True)
class AchievementReward:
    """Payload written to the Ledger upon unlock."""

    ledger_amount: float = 0.0
    description: str = ""


@dataclass(frozen=True)
class AchievementDef:
    """Declarative definition of a single achievement."""

    id: str
    name: str
    description: str
    category: AchievementCategory
    condition: Condition
    reward: AchievementReward
    icon: str = "🏆"
    hidden: bool = False


# ── Condition protocol & built-in primitives ────────────────────


class Condition(Protocol):
    """A condition evaluated against ``EvaluationContext``.

    Implementations must be hashable (frozen dataclasses work well).
    """

    def __call__(self, ctx: EvaluationContext) -> bool: ...


@dataclass(frozen=True)
class EvaluationContext:
    """Snapshot of simulation state for condition evaluation.

    Constructed each tick from ``TickEvents`` + cumulative state.
    """

    tick: int
    tick_in_day: int
    day: int
    trip_count: int  # cumulative completed trips
    completed_trips: list[Any]  # trips completed this tick
    revenue_today: float
    profit_today: float  # running accumulated profit for the current in-progress day
    cumulative_balance: float  # net balance (revenue - costs)
    cumulative_revenue: float = 0.0  # gross cumulative revenue (positive entries only)
    station_inventory: dict[str, int]
    station_capacity: dict[str, int] = field(default_factory=dict)
    daily_profit_history: list[float]  # profit for each completed day
    dispatch_movements: list[tuple[str, str, int]]
    consecutive_trip_count: int = 0  # trips on consecutive non-idle ticks


# ── Condition primitives ────────────────────────────────────────


@dataclass(frozen=True)
class TripCountGe:
    """Cumulative completed trips >= n."""

    n: int

    def __call__(self, ctx: EvaluationContext) -> bool:
        return ctx.trip_count >= self.n


@dataclass(frozen=True)
class RevenueGe:
    """Cumulative gross revenue >= amount.

    Uses ``cumulative_revenue`` (sum of all positive ledger entries),
    not ``cumulative_balance`` which includes costs.
    """

    amount: float

    def __call__(self, ctx: EvaluationContext) -> bool:
        return ctx.cumulative_revenue >= self.amount


@dataclass(frozen=True)
class ProfitTodayGe:
    """Today's profit >= amount."""

    amount: float

    def __call__(self, ctx: EvaluationContext) -> bool:
        return ctx.profit_today >= self.amount


@dataclass(frozen=True)
class Streak:
    """Unlock after *days* consecutive days where *sub_condition* is met.

    The engine maintains streak counters in ``AchievementState.streaks``,
    keyed by the enclosing achievement ``id``.  At each day boundary the
    engine increments the counter if *sub_condition* was satisfied on the
    previous day, otherwise resets it.
    """

    days: int
    sub_condition: Condition

    def __call__(self, ctx: EvaluationContext) -> bool:
        # The engine pre-populates ctx.daily_profit_history; we check
        # whether the last *days* entries all satisfied sub_condition.
        if len(ctx.daily_profit_history) < self.days:
            return False
        # Create a synthetic context for the sub-condition check per day.
        # For day-level sub-conditions (e.g. ProfitTodayGe) we just verify
        # the historical record directly.
        return all(
            self._day_satisfies(profit, ctx, day_offset=i)
            for i, profit in enumerate(reversed(ctx.daily_profit_history[-self.days :]))
        )

    def _day_satisfies(self, profit: float, ctx: EvaluationContext, day_offset: int) -> bool:
        """Check if *sub_condition* was met on a given historical day."""
        from app.core.achievement import ProfitTodayGe

        if isinstance(self.sub_condition, ProfitTodayGe):
            return profit >= self.sub_condition.amount
        # Fallback: create a synthetic context for the historical day
        synth_ctx = EvaluationContext(
            tick=ctx.tick - day_offset * 1440,
            tick_in_day=0,
            day=ctx.day - day_offset - 1,
            trip_count=ctx.trip_count,
            completed_trips=[],
            revenue_today=0.0,
            profit_today=profit,
            cumulative_balance=ctx.cumulative_balance,
            station_inventory=ctx.station_inventory,
            daily_profit_history=[],
            dispatch_movements=ctx.dispatch_movements,
        )
        return self.sub_condition(synth_ctx)


@dataclass(frozen=True)
class ConsecutiveTrips:
    """Complete *n* consecutive trips without idle ticks.

    Uses ``EvaluationContext.consecutive_trip_count`` which the engine
    maintains across ticks — incremented on ticks with completed trips,
    reset to 0 on idle ticks.
    """

    n: int

    def __call__(self, ctx: EvaluationContext) -> bool:
        return ctx.consecutive_trip_count >= self.n


@dataclass(frozen=True)
class StationUtilizationGe:
    """Station inventory / capacity ratio >= *ratio*.

    Requires ``ctx.station_capacity`` to be populated for the target station.
    Falls back to ``inv > 0`` when capacity is unavailable.
    """

    station_id: str
    ratio: float

    def __call__(self, ctx: EvaluationContext) -> bool:
        inv = ctx.station_inventory.get(self.station_id, 0)
        cap = ctx.station_capacity.get(self.station_id, 0)
        if cap > 0:
            return inv / cap >= self.ratio
        # Fallback when capacity is not yet available from TickEvents
        return inv > 0


@dataclass(frozen=True)
class AllOf:
    """All sub-conditions must be satisfied."""

    conditions: tuple[Condition, ...]

    def __call__(self, ctx: EvaluationContext) -> bool:
        return all(c(ctx) for c in self.conditions)


@dataclass(frozen=True)
class AnyOf:
    """At least one sub-condition must be satisfied."""

    conditions: tuple[Condition, ...]

    def __call__(self, ctx: EvaluationContext) -> bool:
        return any(c(ctx) for c in self.conditions)


# ── runtime state ───────────────────────────────────────────────


@dataclass
class StreakTracker:
    """Per-achievement streak counter."""

    key: str
    current_streak: int = 0
    best_streak: int = 0
    last_checked_tick: int = 0


@dataclass
class AchievementState:
    """Runtime tracking state for the engine."""

    unlocked: set[str] = field(default_factory=set)
    streaks: dict[str, StreakTracker] = field(default_factory=dict)
    counters: dict[str, int | float] = field(default_factory=dict)
    tick_last_evaluated: int = 0
    daily_profit_history: list[float] = field(default_factory=list)
    last_day_completed: int = -1
    consecutive_trip_counter: int = 0
    current_day_profit: float = 0.0  # running profit accumulated so far today


# ── the engine ──────────────────────────────────────────────────


class AchievementEngine:
    """Tick-driven achievement engine.

    Usage::

        engine = AchievementEngine(ledger)
        engine.register(*BUILTIN_ACHIEVEMENTS)
        # AchievementEngine.__init__ subscribes to EventBus "tick"
    """

    def __init__(self, ledger: Ledger) -> None:
        self._registry: dict[str, AchievementDef] = {}
        self._state = AchievementState()
        self._ledger = ledger
        self._ticks_per_day = 1440

        # Subscribe to EventBus tick events
        EventBus().subscribe("tick", self._on_tick, key="achievement")

    # ── registration ────────────────────────────────────────────

    def register(self, *defs: AchievementDef) -> None:
        """Register one or more achievement definitions."""
        for d in defs:
            self._registry[d.id] = d

    @property
    def registered_count(self) -> int:
        return len(self._registry)

    @property
    def unlocked_count(self) -> int:
        return len(self._state.unlocked)

    @property
    def state(self) -> AchievementState:
        return self._state

    # ── tick handler ────────────────────────────────────────────

    def _on_tick(self, event: Any) -> None:
        """EventBus handler — evaluate all registered achievements."""
        from app.core.engine import TickEvents

        if not isinstance(event, TickEvents):
            return

        ctx = self._build_context(event)
        self._update_streaks(ctx)
        self._update_consecutive_trips(event)
        new_unlocks: list[AchievementDef] = []

        for defn in self._registry.values():
            if defn.id in self._state.unlocked:
                continue
            if defn.condition(ctx):
                self._state.unlocked.add(defn.id)
                new_unlocks.append(defn)

        # Batch-write unlocks to Ledger
        if new_unlocks:
            entries = [
                LedgerEntry(
                    tick=ctx.tick,
                    entry_id=f"achievement-{d.id}-{ctx.tick}",
                    category=RevenueCategory.ACHIEVEMENT,
                    amount=d.reward.ledger_amount,
                    description=f"🏆 {d.icon} {d.name}: {d.reward.description}",
                )
                for d in new_unlocks
            ]
            self._ledger = self._ledger.append(entries)

        # Track cumulative counters
        self._state.counters["trip_count"] = ctx.trip_count
        self._state.counters["cumulative_balance"] = ctx.cumulative_balance
        self._state.tick_last_evaluated = ctx.tick

    # ── context building ────────────────────────────────────────

    def _build_context(self, event: Any) -> EvaluationContext:
        """Build an ``EvaluationContext`` from a ``TickEvents``."""
        from app.core.engine import TickEvents

        if not isinstance(event, TickEvents):
            return EvaluationContext(
                tick=0,
                tick_in_day=0,
                day=0,
                trip_count=0,
                completed_trips=[],
                revenue_today=0.0,
                profit_today=0.0,
                cumulative_balance=0.0,
                cumulative_revenue=0.0,
                station_inventory={},
                station_capacity={},
                daily_profit_history=[],
                dispatch_movements=[],
                consecutive_trip_count=0,
            )

        tick = event.tick
        tick_in_day = tick % self._ticks_per_day
        day = tick // self._ticks_per_day

        # Completed trips from ledger entries this tick
        completed_trips = [
            e for e in event.ledger_entries
            if isinstance(getattr(e, "category", None), RevenueCategory)
            and e.category == RevenueCategory.TRIP_INCOME
        ]

        # Revenue / profit from this tick's entries
        revenue_this_tick = sum(
            e.amount for e in event.ledger_entries
            if e.amount > 0
        )
        cost_this_tick = abs(sum(
            e.amount for e in event.ledger_entries
            if e.amount < 0
        ))
        profit_this_tick = revenue_this_tick - cost_this_tick

        # Cumulative gross revenue (positive entries only, != net balance)
        cumulative_revenue = float(self._state.counters.get("cumulative_revenue", 0.0)) + revenue_this_tick
        # Cumulative net balance (includes costs)
        cumulative_balance = float(self._state.counters.get("cumulative_balance", 0.0)) + profit_this_tick

        trip_count = int(self._state.counters.get("trip_count", 0)) + len(completed_trips)

        # Day boundary: flush previous day's accumulated profit, then reset
        if tick_in_day == 0 and day > self._state.last_day_completed and tick > 0:
            self._state.daily_profit_history.append(self._state.current_day_profit)
            self._state.last_day_completed = day
            self._state.current_day_profit = 0.0

        # Accumulate profit for the current (in-progress) day
        self._state.current_day_profit += profit_this_tick

        # Update cumulative counters in state for next tick
        self._state.counters["cumulative_revenue"] = cumulative_revenue

        return EvaluationContext(
            tick=tick,
            tick_in_day=tick_in_day,
            day=day,
            trip_count=trip_count,
            completed_trips=completed_trips,
            revenue_today=revenue_this_tick,
            profit_today=self._state.current_day_profit,
            cumulative_balance=cumulative_balance,
            cumulative_revenue=cumulative_revenue,
            station_inventory=event.station_inventory,
            station_capacity={},  # not yet available from TickEvents
            daily_profit_history=list(self._state.daily_profit_history),
            dispatch_movements=event.dispatch_movements,
            consecutive_trip_count=self._state.consecutive_trip_counter,
        )

    # ── streak tracking ─────────────────────────────────────────

    def _update_streaks(self, ctx: EvaluationContext) -> None:
        """Update streak trackers at day boundaries."""
        if ctx.tick_in_day != 0 or ctx.tick == 0:
            return

        for defn in self._registry.values():
            if defn.id in self._state.unlocked:
                continue
            if defn.category != AchievementCategory.STREAK:
                continue
            if not isinstance(defn.condition, Streak):
                continue

            tracker = self._state.streaks.setdefault(
                defn.id,
                StreakTracker(key=defn.id),
            )

            # Check if the sub-condition was met on the PREVIOUS day
            sub = defn.condition.sub_condition
            if sub(ctx):
                tracker.current_streak += 1
                if tracker.current_streak > tracker.best_streak:
                    tracker.best_streak = tracker.current_streak
            else:
                tracker.current_streak = 0

            tracker.last_checked_tick = ctx.tick

    def _update_consecutive_trips(self, event: Any) -> None:
        """Update consecutive-trip counters."""
        from app.core.engine import TickEvents

        if not isinstance(event, TickEvents):
            return

        completed_this_tick = [
            e for e in event.ledger_entries
            if isinstance(getattr(e, "category", None), RevenueCategory)
            and e.category == RevenueCategory.TRIP_INCOME
        ]

        if completed_this_tick:
            self._state.consecutive_trip_counter += len(completed_this_tick)
        else:
            self._state.consecutive_trip_counter = 0

        self._state.counters["consecutive_trips"] = self._state.consecutive_trip_counter


# ── built-in achievements ───────────────────────────────────────


BUILTIN_ACHIEVEMENTS = [
    AchievementDef(
        id="first_trip",
        name="首单骑手",
        description="完成第一笔订单",
        category=AchievementCategory.MILESTONE,
        condition=TripCountGe(1),
        reward=AchievementReward(5.0, "完成第一笔订单"),
        icon="🚴",
    ),
    AchievementDef(
        id="profit_streak_7",
        name="七连盈",
        description="连续7天盈利",
        category=AchievementCategory.STREAK,
        condition=Streak(7, ProfitTodayGe(0.0)),
        reward=AchievementReward(50.0, "连续7天盈利"),
        icon="📈",
    ),
    AchievementDef(
        id="revenue_10k",
        name="营收过万",
        description="累计营收突破 ¥10,000",
        category=AchievementCategory.MILESTONE,
        condition=RevenueGe(10000.0),
        reward=AchievementReward(200.0, "累计营收突破 ¥10,000"),
        icon="💰",
    ),
    AchievementDef(
        id="perfect_dispatch",
        name="完美调度",
        description="连续5次成功调度",
        category=AchievementCategory.MILESTONE,
        condition=ConsecutiveTrips(5),
        reward=AchievementReward(15.0, "连续5次成功调度"),
        icon="🎯",
    ),
]
