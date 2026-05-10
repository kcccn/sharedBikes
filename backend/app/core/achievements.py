"""Achievement system — DSL definitions, engine, and Ledger integration.

Defines three achievement types:
- **Milestone**: triggers once when a cumulative metric crosses a threshold
- **Streak**: triggers when consecutive ticks/days satisfy a predicate
- **Period-end**: triggers at day boundaries when a condition is met

The :class:`AchievementEngine` subscribes to the EventBus ``"tick"`` topic
and evaluates all registered achievements on each tick. Unlocked achievements
with a cash reward are posted to the financial :class:`~app.core.finance.Ledger`
via a ``REVENUE / ACHIEVEMENT_REWARD`` entry.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ── types ────────────────────────────────────────────────────────


class AchievementType(Enum):
    """The three supported achievement kinds."""

    MILESTONE = auto()  # cumulative metric crosses a threshold (fires once)
    STREAK = auto()  # N consecutive days meeting a condition
    PERIOD_END = auto()  # evaluated at daily-report boundaries


# Convenience alias — an evaluator receives the engine state snapshot
# and returns True when the condition is satisfied.
#
# The first argument is always a dict with keys that depend on context:
#
#   MILESTONE  → {"metric": float, "target": float,
#                  "cumulative_value": float, "tick": int}
#   STREAK     → {"day_condition_met": bool, "current_streak": int,
#                  "tick": int}
#   PERIOD_END → {"report": DailyReport, "tick": int}
#
Evaluator = Callable[[dict[str, Any]], bool]


@dataclass(frozen=True)
class AchievementDef:
    """Immutable definition of a single achievement.

    The ``evaluator`` callable is invoked with a context dict (see above).
    For ``MILESTONE`` achievements the engine also checks a threshold-crossing
    guard so the achievement fires at most once.
    """

    id: str
    name: str
    description: str
    type: AchievementType
    evaluator: Evaluator

    # Milestone-specific: the cumulative metric and threshold value.
    # The engine uses these to implement the **fire-once** guarantee:
    # the achievement is unlocked the *first* tick where
    # cumulative_value >= target.
    metric_name: str = ""
    target_value: float = 0.0

    # Streak-specific: required consecutive days
    streak_target: int = 0

    # Optional cash reward posted to the Ledger on unlock
    reward_coins: float = 0.0


# ── runtime state ────────────────────────────────────────────────


@dataclass
class _MilestoneState:
    """Per-achievement runtime for MILESTONE type."""

    unlocked: bool = False
    last_observed_value: float = 0.0


@dataclass
class _StreakState:
    """Per-achievement runtime for STREAK type."""

    unlocked: bool = False
    current_streak: int = 0
    last_day: int = -1  # last day we evaluated


@dataclass
class _PeriodEndState:
    """Per-achievement runtime for PERIOD_END type."""

    unlocked: bool = False
    last_day: int = -1  # last day we evaluated


@dataclass
class _UnlockRecord:
    """Record of a single achievement unlock."""

    achievement_id: str
    tick: int
    reward_coins: float


# ── achievement engine ───────────────────────────────────────────


@dataclass
class AchievementEngine:
    """Event-driven achievement evaluator.

    Usage::

        engine = AchievementEngine(builtin_achievements())
        bus = EventBus.get_instance()
        bus.subscribe("tick", engine.handle_tick, key="achievement")

    The engine examines every tick event and checks whether any achievement
    condition has been newly satisfied. On unlock it optionally posts a
    ``LedgerEntry`` to the financial ledger (via the ``attach_ledger``
    convenience) and records the unlock internally.
    """

    achievements: list[AchievementDef]
    _milestone_state: dict[str, _MilestoneState] = field(default_factory=dict)
    _streak_state: dict[str, _StreakState] = field(default_factory=dict)
    _period_end_state: dict[str, _PeriodEndState] = field(default_factory=dict)
    _unlocked: list[_UnlockRecord] = field(default_factory=list)
    _ledger_entries: list = field(default_factory=list)  # LedgerEntry buffer

    # Optional reference to the financial ledger (set via attach_ledger)
    _ledger: Any = None  # type: ignore[explicit-any]

    def __post_init__(self) -> None:
        """Initialise per-achievement runtime state."""
        for a in self.achievements:
            if a.type == AchievementType.MILESTONE:
                self._milestone_state[a.id] = _MilestoneState()
            elif a.type == AchievementType.STREAK:
                self._streak_state[a.id] = _StreakState()
            elif a.type == AchievementType.PERIOD_END:
                self._period_end_state[a.id] = _PeriodEndState()

    def attach_ledger(self, ledger: Any) -> None:  # type: ignore[explicit-any]
        """Attach a financial :class:`~app.core.finance.Ledger`.

        When attached, unlocked achievements with *reward_coins > 0* will
        automatically post a ``REVENUE / ACHIEVEMENT_REWARD`` entry.
        """
        self._ledger = ledger

    @property
    def unlocked(self) -> list[_UnlockRecord]:
        """All achievement unlock records (chronological)."""
        return list(self._unlocked)

    @property
    def unlocked_ids(self) -> set[str]:
        """Set of achievement IDs that have been unlocked."""
        return {r.achievement_id for r in self._unlocked}

    def is_unlocked(self, achievement_id: str) -> bool:
        """Check whether a specific achievement has been unlocked."""
        return achievement_id in self.unlocked_ids

    def flush_ledger_entries(self) -> list:
        """Return and clear the pending ledger-entry buffer.

        The engine manager calls this after each tick to actually append
        the entries to the financial ledger.
        """
        entries = list(self._ledger_entries)
        self._ledger_entries.clear()
        return entries

    # ── tick handler (registered on EventBus) ────────────────────

    def handle_tick(self, events: Any) -> None:  # type: ignore[explicit-any]
        """EventBus subscriber — evaluate achievements on each tick.

        Signature matches ``TickEventHandler``::

            def handler(tick_events: TickEvents) -> None
        """
        from app.core.finance import LedgerEntry, RevenueCategory

        tick = events.tick
        new_unlocks: list[_UnlockRecord] = []

        # ── MILESTONE: check cumulative metric thresholds ────────
        for ach in self.achievements:
            if ach.type != AchievementType.MILESTONE:
                continue
            state = self._milestone_state[ach.id]
            if state.unlocked:
                continue

            # Build context and evaluate
            ctx = {
                "tick": tick,
                "metric": getattr(events, ach.metric_name, 0.0),
                "target": ach.target_value,
                "cumulative_value": getattr(events, ach.metric_name, 0.0),
            }
            if ach.evaluator(ctx):
                state.unlocked = True
                record = _UnlockRecord(ach.id, tick, ach.reward_coins)
                new_unlocks.append(record)

        # ── STREAK: consecutive day condition ────────────────────
        tick_in_day = tick % 1440
        current_day = tick // 1440

        for ach in self.achievements:
            if ach.type != AchievementType.STREAK:
                continue
            state = self._streak_state[ach.id]
            if state.unlocked:
                continue

            # Evaluate at day boundary (first tick of new day)
            if tick_in_day != 0 and current_day == state.last_day:
                continue

            # Build context — is the day condition met?
            ctx = {
                "tick": tick,
                "day_condition_met": False,  # evaluator will refine
                "current_streak": state.current_streak,
            }
            day_met = ach.evaluator(ctx)
            state.last_day = current_day

            if day_met:
                state.current_streak += 1
                if state.current_streak >= ach.streak_target:
                    state.unlocked = True
                    record = _UnlockRecord(ach.id, tick, ach.reward_coins)
                    new_unlocks.append(record)
            else:
                state.current_streak = 0

        # ── PERIOD_END: evaluate at daily-report boundaries ──────
        for ach in self.achievements:
            if ach.type != AchievementType.PERIOD_END:
                continue
            state = self._period_end_state[ach.id]
            if state.unlocked:
                continue

            if tick_in_day != 0 and current_day == state.last_day:
                continue

            # Check if this tick marks a day boundary (tick_in_day == 0)
            if tick_in_day != 0:
                continue

            # Build context — the DailyReport associated with this boundary
            ctx = {
                "tick": tick,
                "report": getattr(events, "_daily_report", None),
            }
            if ach.evaluator(ctx):
                state.unlocked = True
                record = _UnlockRecord(ach.id, tick, ach.reward_coins)
                new_unlocks.append(record)

            state.last_day = current_day

        # ── record unlocks + post ledger entries ─────────────────
        for record in new_unlocks:
            self._unlocked.append(record)
            logger.info(
                "Achievement unlocked: %s (tick %d, reward ¥%.2f)",
                record.achievement_id,
                record.tick,
                record.reward_coins,
            )
            if record.reward_coins > 0:
                entry = LedgerEntry(
                    tick=record.tick,
                    entry_id=f"ach_{record.achievement_id}_{record.tick}",
                    category=RevenueCategory.ACHIEVEMENT_REWARD,
                    amount=record.reward_coins,
                    description=f"Achievement unlocked: {record.achievement_id}",
                )
                self._ledger_entries.append(entry)
                if self._ledger is not None:
                    self._ledger.append([entry])

    # ── reset (for test isolation) ───────────────────────────────

    def reset(self) -> None:
        """Clear all runtime state (useful in tests)."""
        self._milestone_state.clear()
        self._streak_state.clear()
        self._period_end_state.clear()
        self._unlocked.clear()
        self._ledger_entries.clear()
        self.__post_init__()


# ── built-in achievements ───────────────────────────────────────


def cumulative_revenue_evaluator(ctx: dict[str, Any]) -> bool:
    """Evaluator: cumulative revenue >= target."""
    return ctx["cumulative_value"] >= ctx["target"]


def cumulative_profit_evaluator(ctx: dict[str, Any]) -> bool:
    """Evaluator: cumulative profit >= target."""
    return ctx["cumulative_value"] >= ctx["target"]


def profitable_day_evaluator(ctx: dict[str, Any]) -> bool:
    """Evaluator: the day's profit was positive."""
    # For streak evaluators, the caller sets day_condition_met
    return ctx.get("day_condition_met", False)


def balance_above_threshold_evaluator(ctx: dict[str, Any]) -> bool:
    """Evaluator: daily report shows cumulative balance above threshold."""
    report = ctx.get("report")
    if report is None:
        return False
    threshold = ctx.get("target", 0.0)
    return report.cumulative_balance >= threshold


def no_alert_evaluator(ctx: dict[str, Any]) -> bool:
    """Evaluator: daily report has no alert (clean day)."""
    report = ctx.get("report")
    if report is None:
        return False
    return report.alert == ""


def builtin_achievements() -> list[AchievementDef]:
    """Return the set of built-in achievements for CityBike-Sim.

    These can be extended or replaced with custom definitions.
    """
    return [
        # ── MILESTONE achievements ───────────────────────────────
        AchievementDef(
            id="first_revenue",
            name="第一桶金",
            description="累计营收达到 ¥10,000",
            type=AchievementType.MILESTONE,
            evaluator=cumulative_revenue_evaluator,
            metric_name="revenue",
            target_value=10_000,
            reward_coins=500,
        ),
        AchievementDef(
            id="traffic_king",
            name="营收之王",
            description="累计营收达到 ¥100,000",
            type=AchievementType.MILESTONE,
            evaluator=cumulative_revenue_evaluator,
            metric_name="revenue",
            target_value=100_000,
            reward_coins=5000,
        ),
        AchievementDef(
            id="profitable",
            name="扭亏为盈",
            description="累计利润达到 ¥50,000",
            type=AchievementType.MILESTONE,
            evaluator=cumulative_profit_evaluator,
            metric_name="profit",
            target_value=50_000,
            reward_coins=2000,
        ),
        # ── STREAK achievements ──────────────────────────────────
        AchievementDef(
            id="steady_hand",
            name="稳步经营",
            description="连续 5 天保持盈利",
            type=AchievementType.STREAK,
            evaluator=profitable_day_evaluator,
            streak_target=5,
            reward_coins=1000,
        ),
        AchievementDef(
            id="golden_week",
            name="黄金周",
            description="连续 7 天保持盈利",
            type=AchievementType.STREAK,
            evaluator=profitable_day_evaluator,
            streak_target=7,
            reward_coins=2000,
        ),
        # ── PERIOD_END achievements ──────────────────────────────
        AchievementDef(
            id="mighty_balance",
            name="财力雄厚",
            description="日终余额超过 ¥20,000",
            type=AchievementType.PERIOD_END,
            evaluator=balance_above_threshold_evaluator,
            target_value=20_000,
            reward_coins=1000,
        ),
        AchievementDef(
            id="smooth_sailing",
            name="一帆风顺",
            description="日终无任何预警",
            type=AchievementType.PERIOD_END,
            evaluator=no_alert_evaluator,
            reward_coins=500,
        ),
    ]
