"""Tests for the Achievement DSL and AchievementEngine."""

import pytest
from app.core.achievements import (
    AchievementDef,
    AchievementEngine,
    AchievementType,
    _UnlockRecord,
    builtin_achievements,
    cumulative_revenue_evaluator,
    profitable_day_evaluator,
    balance_above_threshold_evaluator,
    no_alert_evaluator,
)
from app.core.event_bus import EventBus, TickEvents


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_bus():
    EventBus.reset_instance()
    yield
    EventBus.reset_instance()


@pytest.fixture
def empty_engine():
    return AchievementEngine(achievements=[])


@pytest.fixture
def milestone_engine():
    """Engine with a single milestone: revenue >= 500."""
    ach = AchievementDef(
        id="test_milestone",
        name="Test Milestone",
        description="Earn 500 revenue",
        type=AchievementType.MILESTONE,
        evaluator=cumulative_revenue_evaluator,
        metric_name="revenue",
        target_value=500,
        reward_coins=100,
    )
    return AchievementEngine(achievements=[ach])


@pytest.fixture
def streak_engine():
    """Engine with a streak: 3 consecutive profitable days."""
    ach = AchievementDef(
        id="test_streak",
        name="Test Streak",
        description="3 profitable days in a row",
        type=AchievementType.STREAK,
        evaluator=profitable_day_evaluator,
        streak_target=3,
        reward_coins=200,
    )
    return AchievementEngine(achievements=[ach])


@pytest.fixture
def period_end_engine():
    """Engine with a period-end check: balance >= 1000 at day boundary."""
    ach = AchievementDef(
        id="test_period_end",
        name="Test Period End",
        description="Balance >= 1000 at day end",
        type=AchievementType.PERIOD_END,
        evaluator=balance_above_threshold_evaluator,
        target_value=1000,
        reward_coins=300,
    )
    return AchievementEngine(achievements=[ach])


def make_tick_events(tick, revenue=0, profit=0):
    """Helper to build a TickEvents-like object."""
    class FakeEntry:
        def __init__(self, amount):
            self.amount = amount

    entries = []
    if revenue:
        entries.append(FakeEntry(revenue))
    if profit:
        entries.append(FakeEntry(profit))

    ev = TickEvents(tick=tick, time_of_day="00:00", ledger_entries=entries)
    ev.revenue = revenue
    ev.profit = profit
    return ev


def make_day_boundary(tick, report=None):
    """Helper to build a TickEvents at day boundary (tick % 1440 == 0)."""
    ev = make_tick_events(tick)
    ev._daily_report = report
    return ev


# ---------------------------------------------------------------------------
# AchievementDef basics
# ---------------------------------------------------------------------------

class TestAchievementDef:
    def test_basic_milestone_def(self):
        ach = AchievementDef(
            id="m1", name="M1", description="",
            type=AchievementType.MILESTONE,
            evaluator=lambda ctx: True,
            metric_name="revenue", target_value=100,
        )
        assert ach.id == "m1"
        assert ach.type == AchievementType.MILESTONE

    def test_basic_streak_def(self):
        ach = AchievementDef(
            id="s1", name="S1", description="",
            type=AchievementType.STREAK,
            evaluator=lambda ctx: True,
            streak_target=5,
        )
        assert ach.type == AchievementType.STREAK
        assert ach.streak_target == 5

    def test_basic_period_end_def(self):
        ach = AchievementDef(
            id="p1", name="P1", description="",
            type=AchievementType.PERIOD_END,
            evaluator=lambda ctx: True,
        )
        assert ach.type == AchievementType.PERIOD_END


# ---------------------------------------------------------------------------
# Empty engine
# ---------------------------------------------------------------------------

class TestEmptyEngine:
    def test_no_achievements_no_unlocks(self, empty_engine):
        ev = make_tick_events(tick=1)
        empty_engine.handle_tick(ev)
        assert empty_engine.unlocked == []

    def test_is_unlocked_returns_false(self, empty_engine):
        assert not empty_engine.is_unlocked("nonexistent")


# ---------------------------------------------------------------------------
# MILESTONE achievements
# ---------------------------------------------------------------------------

class TestMilestone:
    def test_unlock_when_revenue_crosses_threshold(self, milestone_engine):
        ev = make_tick_events(tick=10, revenue=600)
        milestone_engine.handle_tick(ev)
        assert milestone_engine.is_unlocked("test_milestone")

    def test_no_unlock_below_threshold(self, milestone_engine):
        ev = make_tick_events(tick=10, revenue=400)
        milestone_engine.handle_tick(ev)
        assert not milestone_engine.is_unlocked("test_milestone")

    def test_unlock_once_not_retriggered(self, milestone_engine):
        ev1 = make_tick_events(tick=10, revenue=600)
        milestone_engine.handle_tick(ev1)
        assert milestone_engine.is_unlocked("test_milestone")
        assert len(milestone_engine.unlocked) == 1

        ev2 = make_tick_events(tick=20, revenue=1000)
        milestone_engine.handle_tick(ev2)
        assert len(milestone_engine.unlocked) == 1

    def test_reward_coins_create_ledger_entry(self, milestone_engine):
        from app.core.finance import RevenueCategory

        ev = make_tick_events(tick=10, revenue=600)
        milestone_engine.handle_tick(ev)

        assert len(milestone_engine._ledger_entries) == 1
        entry = milestone_engine._ledger_entries[0]
        assert entry.amount == 100
        assert entry.category == RevenueCategory.ACHIEVEMENT_REWARD

    def test_zero_reward_no_ledger_entry(self):
        ach = AchievementDef(
            id="free", name="Free", description="",
            type=AchievementType.MILESTONE,
            evaluator=cumulative_revenue_evaluator,
            metric_name="revenue", target_value=10,
            reward_coins=0,
        )
        engine = AchievementEngine(achievements=[ach])
        ev = make_tick_events(tick=1, revenue=50)
        engine.handle_tick(ev)
        assert engine._ledger_entries == []


# ---------------------------------------------------------------------------
# STREAK achievements
# ---------------------------------------------------------------------------

class TestStreak:
    def test_unlock_after_streak_target_met(self, streak_engine):
        TPD = 1440
        for day in range(3):
            tick = (day + 1) * TPD
            ctx = {"tick": tick, "day_condition_met": True, "current_streak": 0}
            ev = make_tick_events(tick)
            ev.revenue = 1000
            ev.profit = 500
            streak_engine.handle_tick(ev)

        assert streak_engine.is_unlocked("test_streak")

    def test_streak_broken_no_unlock(self, streak_engine):
        TPD = 1440
        for day in range(2):
            tick = (day + 1) * TPD
            ev = make_tick_events(tick)
            streak_engine.handle_tick(ev)

        assert not streak_engine.is_unlocked("test_streak")

    def test_reward_on_streak_unlock(self, streak_engine):
        TPD = 1440
        from app.core.finance import RevenueCategory

        for day in range(3):
            tick = (day + 1) * TPD
            ev = make_tick_events(tick)
            ev.revenue = 1000
            ev.profit = 500
            streak_engine.handle_tick(ev)

        entries = streak_engine._ledger_entries
        assert len(entries) == 1
        assert entries[0].category == RevenueCategory.ACHIEVEMENT_REWARD


# ---------------------------------------------------------------------------
# PERIOD_END achievements
# ---------------------------------------------------------------------------

class TestPeriodEnd:
    def test_unlock_at_day_boundary(self, period_end_engine):
        TPD = 1440

        class FakeReport:
            def __init__(self):
                self.cumulative_balance = 2000
                self.alert = ""

        ev = make_day_boundary(TPD, report=FakeReport())
        period_end_engine.handle_tick(ev)
        assert period_end_engine.is_unlocked("test_period_end")

    def test_no_unlock_below_threshold(self, period_end_engine):
        TPD = 1440

        class FakeReport:
            def __init__(self):
                self.cumulative_balance = 500
                self.alert = ""

        ev = make_day_boundary(TPD, report=FakeReport())
        period_end_engine.handle_tick(ev)
        assert not period_end_engine.is_unlocked("test_period_end")

    def test_no_unlock_on_non_boundary(self, period_end_engine):
        ev = make_day_boundary(1)  # tick 1 is not a day boundary
        period_end_engine.handle_tick(ev)
        assert not period_end_engine.is_unlocked("test_period_end")


# ---------------------------------------------------------------------------
# EventBus integration
# ---------------------------------------------------------------------------

class TestEventBusIntegration:
    def test_engine_subscribes_and_receives_ticks(self, milestone_engine):
        bus = EventBus()
        bus.subscribe("tick", milestone_engine.handle_tick, key="achievement")

        ev = make_tick_events(tick=1, revenue=600)
        bus.publish("tick", ev)

        assert milestone_engine.is_unlocked("test_milestone")

    def test_key_replaced_on_resubscribe(self, milestone_engine):
        bus = EventBus()
        bus.subscribe("tick", milestone_engine.handle_tick, key="achievement")

        results = []
        bus.subscribe("tick", lambda e: results.append("new"), key="achievement")
        ev = make_tick_events(tick=1, revenue=600)
        bus.publish("tick", ev)

        # Old handler (milestone_engine) should NOT be called
        assert not milestone_engine.is_unlocked("test_milestone")
        assert results == ["new"]


# ---------------------------------------------------------------------------
# Ledger attachment
# ---------------------------------------------------------------------------

class TestLedgerIntegration:
    def test_attach_ledger_posts_entries(self, milestone_engine):
        from app.core.finance import Ledger, RevenueCategory

        ledger = Ledger()
        milestone_engine.attach_ledger(ledger)

        ev = make_tick_events(tick=10, revenue=600)
        milestone_engine.handle_tick(ev)

        assert len(milestone_engine._ledger_entries) == 1
        entry = milestone_engine._ledger_entries[0]
        assert entry.category == RevenueCategory.ACHIEVEMENT_REWARD
        assert entry.amount == 100


# ---------------------------------------------------------------------------
# Built-in achievements
# ---------------------------------------------------------------------------

class TestBuiltinAchievements:
    def test_builtin_list_not_empty(self):
        achs = builtin_achievements()
        assert len(achs) >= 5

    def test_all_have_unique_ids(self):
        achs = builtin_achievements()
        ids = [a.id for a in achs]
        assert len(ids) == len(set(ids))

    def test_first_revenue_has_correct_target(self):
        achs = builtin_achievements()
        fr = next(a for a in achs if a.id == "first_revenue")
        assert fr.target_value == 10_000
        assert fr.reward_coins == 500

    def test_steady_hand_streak_target(self):
        achs = builtin_achievements()
        sh = next(a for a in achs if a.id == "steady_hand")
        assert sh.streak_target == 5


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_reset_clears_state(self, milestone_engine):
        ev = make_tick_events(tick=10, revenue=600)
        milestone_engine.handle_tick(ev)
        assert milestone_engine.is_unlocked("test_milestone")
        assert len(milestone_engine._ledger_entries) == 1

        milestone_engine.reset()
        assert not milestone_engine.is_unlocked("test_milestone")
        assert milestone_engine._ledger_entries == []

    def test_handle_tick_no_crash_on_missing_attributes(self, empty_engine):
        ev = make_tick_events(tick=1)
        empty_engine.handle_tick(ev)
        assert empty_engine.unlocked == []

    def test_flush_ledger_entries(self, milestone_engine):
        ev = make_tick_events(tick=10, revenue=600)
        milestone_engine.handle_tick(ev)
        entries = milestone_engine.flush_ledger_entries()
        assert len(entries) == 1
        assert milestone_engine._ledger_entries == []

    def test_unlocked_records_are_chronological(self):
        achs = [
            AchievementDef(
                id=f"m{i}", name=f"M{i}", description="",
                type=AchievementType.MILESTONE,
                evaluator=cumulative_revenue_evaluator,
                metric_name="revenue", target_value=100 * i,
                reward_coins=10,
            )
            for i in range(1, 4)
        ]
        engine = AchievementEngine(achievements=achs)
        ev = make_tick_events(tick=5, revenue=999)
        engine.handle_tick(ev)

        assert len(engine.unlocked) == 3
        assert engine.unlocked[0].achievement_id == "m1"
        assert engine.unlocked[2].achievement_id == "m3"
