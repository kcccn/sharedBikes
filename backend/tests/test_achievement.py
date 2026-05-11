"""Tests for the AchievementEngine (achievement.py)."""

from app.core.achievement import (
    AchievementCategory,
    AchievementDef,
    AchievementEngine,
    AchievementReward,
    AchievementUnlockState,
    BUILTIN_ACHIEVEMENTS,
    AllOf,
    AnyOf,
    ConsecutiveTrips,
    EvaluationContext,
    ProfitTodayGe,
    RevenueGe,
    StationUtilizationGe,
    Streak,
    TripCountGe,
)
from app.core.engine import TickEvents
from app.core.event_bus import EventBus
from app.core.finance import Ledger, LedgerEntry, RevenueCategory


# ── helpers ─────────────────────────────────────────────────────


def _make_ctx(
    tick: int = 1,
    trip_count: int = 0,
    profit_today: float = 0.0,
    cumulative_balance: float = 0.0,
    cumulative_revenue: float = 0.0,
    daily_profit_history: list[float] | None = None,
    consecutive_trip_count: int = 0,
    station_inventory: dict[str, int] | None = None,
    station_capacity: dict[str, int] | None = None,
) -> EvaluationContext:
    return EvaluationContext(
        tick=tick,
        tick_in_day=tick % 1440,
        day=tick // 1440,
        trip_count=trip_count,
        completed_trips=[],
        revenue_today=0.0,
        profit_today=profit_today,
        cumulative_balance=cumulative_balance,
        cumulative_revenue=cumulative_revenue,
        station_inventory=station_inventory or {},
        station_capacity=station_capacity or {},
        daily_profit_history=daily_profit_history or [],
        dispatch_movements=[],
        consecutive_trip_count=consecutive_trip_count,
    )


def _make_tick_event(tick: int, entries: list | None = None) -> TickEvents:
    return TickEvents(
        tick=tick,
        time_of_day=f"{tick % 1440 // 60:02d}:{tick % 60:02d}",
        trips=[],
        ledger_entries=entries or [],
        station_inventory={},
        dispatch_movements=[],
    )


# ── Condition primitives ────────────────────────────────────────


class TestTripCountGe:
    def test_below_threshold(self) -> None:
        c = TripCountGe(5)
        ctx = _make_ctx(trip_count=3)
        assert not c(ctx)

    def test_at_threshold(self) -> None:
        c = TripCountGe(5)
        ctx = _make_ctx(trip_count=5)
        assert c(ctx)

    def test_above_threshold(self) -> None:
        c = TripCountGe(5)
        ctx = _make_ctx(trip_count=10)
        assert c(ctx)


class TestRevenueGe:
    def test_below(self) -> None:
        c = RevenueGe(100.0)
        ctx = _make_ctx(cumulative_revenue=50.0)
        assert not c(ctx)

    def test_at_threshold(self) -> None:
        c = RevenueGe(100.0)
        ctx = _make_ctx(cumulative_revenue=100.0)
        assert c(ctx)


class TestProfitTodayGe:
    def test_negative_not_ok(self) -> None:
        c = ProfitTodayGe(0.0)
        ctx = _make_ctx(profit_today=-10.0)
        assert not c(ctx)

    def test_zero_is_profitable(self) -> None:
        c = ProfitTodayGe(0.0)
        ctx = _make_ctx(profit_today=0.0)
        assert c(ctx)

    def test_positive(self) -> None:
        c = ProfitTodayGe(50.0)
        ctx = _make_ctx(profit_today=75.0)
        assert c(ctx)


class TestStreak:
    def test_not_enough_days(self) -> None:
        c = Streak(7, ProfitTodayGe(0.0))
        ctx = _make_ctx(daily_profit_history=[1.0] * 3)
        assert not c(ctx)

    def test_meets_streak(self) -> None:
        c = Streak(3, ProfitTodayGe(0.0))
        ctx = _make_ctx(daily_profit_history=[1.0, 2.0, 3.0])
        assert c(ctx)

    def test_break_in_streak(self) -> None:
        c = Streak(3, ProfitTodayGe(0.0))
        ctx = _make_ctx(daily_profit_history=[1.0, -1.0, 3.0])
        assert not c(ctx)


class TestConsecutiveTrips:
    def test_below(self) -> None:
        c = ConsecutiveTrips(5)
        ctx = _make_ctx(consecutive_trip_count=3)
        assert not c(ctx)

    def test_at_threshold(self) -> None:
        c = ConsecutiveTrips(3)
        ctx = _make_ctx(consecutive_trip_count=3)
        assert c(ctx)

    def test_above_threshold(self) -> None:
        c = ConsecutiveTrips(3)
        ctx = _make_ctx(consecutive_trip_count=5)
        assert c(ctx)


class TestStationUtilizationGe:
    def test_station_empty(self) -> None:
        c = StationUtilizationGe("S1", 0.5)
        ctx = _make_ctx(station_inventory={"S1": 0}, station_capacity={"S1": 10})
        assert not c(ctx)

    def test_below_ratio(self) -> None:
        c = StationUtilizationGe("S1", 0.5)
        ctx = _make_ctx(station_inventory={"S1": 2}, station_capacity={"S1": 10})
        assert not c(ctx)

    def test_at_ratio(self) -> None:
        c = StationUtilizationGe("S1", 0.5)
        ctx = _make_ctx(station_inventory={"S1": 5}, station_capacity={"S1": 10})
        assert c(ctx)

    def test_above_ratio(self) -> None:
        c = StationUtilizationGe("S1", 0.5)
        ctx = _make_ctx(station_inventory={"S1": 8}, station_capacity={"S1": 10})
        assert c(ctx)

    def test_fallback_no_capacity(self) -> None:
        """Without capacity data, falls back to inv > 0."""
        c = StationUtilizationGe("S1", 0.5)
        ctx = _make_ctx(station_inventory={"S1": 1})
        assert c(ctx)


class TestAllOf:
    def test_all_true(self) -> None:
        c = AllOf((TripCountGe(1), RevenueGe(10.0)))
        ctx = _make_ctx(trip_count=5, cumulative_revenue=50.0)
        assert c(ctx)

    def test_one_false(self) -> None:
        c = AllOf((TripCountGe(10), RevenueGe(10.0)))
        ctx = _make_ctx(trip_count=5, cumulative_revenue=50.0)
        assert not c(ctx)


class TestAnyOf:
    def test_one_true(self) -> None:
        c = AnyOf((TripCountGe(10), RevenueGe(10.0)))
        ctx = _make_ctx(trip_count=5, cumulative_revenue=50.0)
        assert c(ctx)

    def test_none_true(self) -> None:
        c = AnyOf((TripCountGe(10), RevenueGe(200.0)))
        ctx = _make_ctx(trip_count=5, cumulative_revenue=50.0)
        assert not c(ctx)


# ── AchievementDef ──────────────────────────────────────────────


class TestAchievementDef:
    def test_def_creation(self) -> None:
        defn = AchievementDef(
            id="test_ach",
            name="测试成就",
            description="测试用",
            category=AchievementCategory.MILESTONE,
            condition=TripCountGe(1),
            reward=AchievementReward(10.0, "奖励"),
            icon="🎯",
        )
        assert defn.id == "test_ach"
        assert defn.name == "测试成就"
        assert defn.reward.ledger_amount == 10.0
        assert not defn.hidden

    def test_default_icon(self) -> None:
        defn = AchievementDef(
            id="no_icon",
            name="No Icon",
            description="",
            category=AchievementCategory.MILESTONE,
            condition=TripCountGe(1),
            reward=AchievementReward(),
        )
        assert defn.icon == "🏆"


# ── BUILTIN_ACHIEVEMENTS ────────────────────────────────────────


class TestBuiltinAchievements:
    def test_first_trip_condition(self) -> None:
        ach = next(a for a in BUILTIN_ACHIEVEMENTS if a.id == "first_trip")
        assert ach.category == AchievementCategory.MILESTONE
        assert not ach.condition(_make_ctx(trip_count=0))
        assert ach.condition(_make_ctx(trip_count=1))

    def test_revenue_10k_condition(self) -> None:
        ach = next(a for a in BUILTIN_ACHIEVEMENTS if a.id == "revenue_10k")
        assert not ach.condition(_make_ctx(cumulative_revenue=5000.0))
        assert ach.condition(_make_ctx(cumulative_revenue=10000.0))

    def test_profit_streak_7_condition(self) -> None:
        ach = next(a for a in BUILTIN_ACHIEVEMENTS if a.id == "profit_streak_7")
        assert ach.category == AchievementCategory.STREAK
        # Not enough days
        assert not ach.condition(_make_ctx(daily_profit_history=[1.0] * 3))
        # Enough profitable days
        assert ach.condition(_make_ctx(daily_profit_history=[1.0] * 7))

    def test_perfect_dispatch_condition(self) -> None:
        ach = next(a for a in BUILTIN_ACHIEVEMENTS if a.id == "perfect_dispatch")
        assert not ach.condition(_make_ctx(consecutive_trip_count=3))
        assert ach.condition(_make_ctx(consecutive_trip_count=5))
        assert ach.condition(_make_ctx(consecutive_trip_count=10))

    def test_all_builtin_have_rewards(self) -> None:
        for ach in BUILTIN_ACHIEVEMENTS:
            assert ach.reward is not None


# ── AchievementEngine ───────────────────────────────────────────

class TestAchievementEngine:
    def setup_method(self) -> None:
        EventBus.reset_instance()
        self.ledger = Ledger()
        self.engine = AchievementEngine(self.ledger)

    def test_register_single(self) -> None:
        defn = AchievementDef(
            id="test", name="Test", description="",
            category=AchievementCategory.MILESTONE,
            condition=TripCountGe(1),
            reward=AchievementReward(5.0, "test"),
        )
        self.engine.register(defn)
        assert self.engine.registered_count == 1
        assert self.engine.unlocked_count == 0

    def test_register_multiple(self) -> None:
        self.engine.register(*BUILTIN_ACHIEVEMENTS)
        assert self.engine.registered_count == 4

    def test_tick_does_not_unlock_without_condition(self) -> None:
        defn = AchievementDef(
            id="test", name="Test", description="",
            category=AchievementCategory.MILESTONE,
            condition=TripCountGe(100),
            reward=AchievementReward(5.0, "test"),
        )
        self.engine.register(defn)
        event = _make_tick_event(tick=1)
        self.engine._on_tick(event)
        assert self.engine.unlocked_count == 0

    def test_tick_unlocks_when_condition_met(self) -> None:
        defn = AchievementDef(
            id="test", name="Test", description="",
            category=AchievementCategory.MILESTONE,
            condition=TripCountGe(1),
            reward=AchievementReward(5.0, "test reward"),
        )
        self.engine.register(defn)
        self.engine._state.counters["trip_count"] = 1
        event = _make_tick_event(tick=1)
        self.engine._on_tick(event)
        assert self.engine.unlocked_count == 1
        assert "test" in self.engine._state.unlocked

    def test_unlock_writes_to_ledger(self) -> None:
        defn = AchievementDef(
            id="test", name="Test", description="",
            category=AchievementCategory.MILESTONE,
            condition=TripCountGe(1),
            reward=AchievementReward(10.0, "reward"),
        )
        self.engine.register(defn)
        self.engine._state.counters["trip_count"] = 1
        event = _make_tick_event(tick=5)
        self.engine._on_tick(event)

        # Check Ledger has the achievement entry
        entries = self.engine._ledger.query(
            category=RevenueCategory.ACHIEVEMENT,
        )
        assert len(entries) == 1
        assert entries[0].amount == 10.0
        assert entries[0].tick == 5
        assert entries[0].entry_id == "achievement-test-5"

    def test_does_not_unlock_twice(self) -> None:
        defn = AchievementDef(
            id="test", name="Test", description="",
            category=AchievementCategory.MILESTONE,
            condition=TripCountGe(1),
            reward=AchievementReward(5.0, "test"),
        )
        self.engine.register(defn)
        self.engine._state.counters["trip_count"] = 1
        self.engine._on_tick(_make_tick_event(tick=1))
        assert self.engine.unlocked_count == 1

        # Second tick — condition still true, but already unlocked
        ledger_len_before = len(self.engine._ledger)
        self.engine._on_tick(_make_tick_event(tick=2))
        assert self.engine.unlocked_count == 1
        assert len(self.engine._ledger) == ledger_len_before  # no duplicate entry

    def test_builtin_achievements_unlock(self) -> None:
        self.engine.register(*BUILTIN_ACHIEVEMENTS)
        self.engine._state.counters["trip_count"] = 10
        self.engine._state.counters["cumulative_balance"] = 15000.0
        self.engine._state.counters["cumulative_revenue"] = 15000.0
        self.engine._state.daily_profit_history = [1.0] * 7

        event = _make_tick_event(tick=1440, entries=[
            LedgerEntry(tick=1440, entry_id="t1", category=RevenueCategory.TRIP_INCOME, amount=5.0),
            LedgerEntry(tick=1440, entry_id="t2", category=RevenueCategory.TRIP_INCOME, amount=5.0),
            LedgerEntry(tick=1440, entry_id="t3", category=RevenueCategory.TRIP_INCOME, amount=5.0),
            LedgerEntry(tick=1440, entry_id="t4", category=RevenueCategory.TRIP_INCOME, amount=5.0),
            LedgerEntry(tick=1440, entry_id="t5", category=RevenueCategory.TRIP_INCOME, amount=5.0),
        ])
        self.engine._on_tick(event)

        # first_trip: trip_count>=1
        assert "first_trip" in self.engine._state.unlocked
        # revenue_10k: cumulative_revenue>=10000
        assert "revenue_10k" in self.engine._state.unlocked
        # profit_streak_7: 7 profitable days in history
        assert "profit_streak_7" in self.engine._state.unlocked
        # perfect_dispatch: 5 consecutive trips
        assert "perfect_dispatch" in self.engine._state.unlocked

    # ── engine-level integration: consecutive trips ─────────────

    def test_consecutive_trips_through_ticks(self) -> None:
        """Verify ConsecutiveTrips counts through actual tick events with idle gaps."""
        self.engine.register(
            AchievementDef(
                id="consec3", name="Consec3", description="",
                category=AchievementCategory.MILESTONE,
                condition=ConsecutiveTrips(3),
                reward=AchievementReward(10.0, "3 consecutive"),
            )
        )

        # Tick 1: one completed trip (TRIP_INCOME)
        e1 = _make_tick_event(tick=1, entries=[
            LedgerEntry(tick=1, entry_id="t1", category=RevenueCategory.TRIP_INCOME, amount=5.0),
        ])
        self.engine._on_tick(e1)
        assert self.engine._state.consecutive_trip_counter == 1
        assert "consec3" not in self.engine._state.unlocked

        # Tick 2: two completed trips (still consecutive)
        e2 = _make_tick_event(tick=2, entries=[
            LedgerEntry(tick=2, entry_id="t2", category=RevenueCategory.TRIP_INCOME, amount=3.0),
            LedgerEntry(tick=2, entry_id="t3", category=RevenueCategory.TRIP_INCOME, amount=4.0),
        ])
        self.engine._on_tick(e2)
        assert self.engine._state.consecutive_trip_counter == 3  # 1 + 2
        assert "consec3" in self.engine._state.unlocked

    def test_consecutive_trips_reset_on_idle(self) -> None:
        """Verify idle tick resets the consecutive counter."""
        self.engine.register(
            AchievementDef(
                id="consec3", name="Consec3", description="",
                category=AchievementCategory.MILESTONE,
                condition=ConsecutiveTrips(3),
                reward=AchievementReward(10.0, "3 consecutive"),
            )
        )

        # Tick 1: trip
        e1 = _make_tick_event(tick=1, entries=[
            LedgerEntry(tick=1, entry_id="t1", category=RevenueCategory.TRIP_INCOME, amount=5.0),
        ])
        self.engine._on_tick(e1)
        assert self.engine._state.consecutive_trip_counter == 1

        # Tick 2: idle — no trips → counter resets to 0
        e2 = _make_tick_event(tick=2, entries=[])
        self.engine._on_tick(e2)
        assert self.engine._state.consecutive_trip_counter == 0

        # Tick 3: trip again — starts from 1, not 2
        e3 = _make_tick_event(tick=3, entries=[
            LedgerEntry(tick=3, entry_id="t3", category=RevenueCategory.TRIP_INCOME, amount=5.0),
        ])
        self.engine._on_tick(e3)
        assert self.engine._state.consecutive_trip_counter == 1
        assert "consec3" not in self.engine._state.unlocked

    # ── engine-level integration: day-boundary profit ───────────

    def test_daily_profit_accumulation_and_flush(self) -> None:
        """Verify profit accumulates across ticks and flushes at day boundary."""
        self.engine.register(
            AchievementDef(
                id="profit50", name="Profit50", description="",
                category=AchievementCategory.MILESTONE,
                condition=ProfitTodayGe(50.0),
                reward=AchievementReward(10.0, "50 profit in a day"),
            )
        )

        # Tick 100 (day 0, mid-day): earn 30
        e1 = _make_tick_event(tick=100, entries=[
            LedgerEntry(tick=100, entry_id="e1", category=RevenueCategory.TRIP_INCOME, amount=30.0),
        ])
        self.engine._on_tick(e1)
        assert self.engine._state.current_day_profit == 30.0
        assert "profit50" not in self.engine._state.unlocked

        # Tick 200 (day 0, still): earn 25 more → accumulated 55
        e2 = _make_tick_event(tick=200, entries=[
            LedgerEntry(tick=200, entry_id="e2", category=RevenueCategory.TRIP_INCOME, amount=25.0),
        ])
        self.engine._on_tick(e2)
        assert self.engine._state.current_day_profit == 55.0
        # ProfitTodayGe checks accumulated profit_today
        assert "profit50" in self.engine._state.unlocked

        # Tick 1440 (day 1, day boundary): flush day 0's profit to history
        assert len(self.engine._state.daily_profit_history) == 0
        e3 = _make_tick_event(tick=1440, entries=[
            LedgerEntry(tick=1440, entry_id="e3", category=RevenueCategory.TRIP_INCOME, amount=10.0),
        ])
        self.engine._on_tick(e3)
        # Day 0's accumulated profit (55.0) was flushed
        assert len(self.engine._state.daily_profit_history) == 1
        assert self.engine._state.daily_profit_history[0] == 55.0
        # current_day_profit reset and now has tick 1440's 10.0
        assert self.engine._state.current_day_profit == 10.0
