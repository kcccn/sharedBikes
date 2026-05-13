"""Dedicated unit tests for GameSession (Phase C)."""

from __future__ import annotations

import pytest

from app.services.game_session import (
    BUY_BIKE_COST,
    EXPAND_STATION_COST,
    INITIAL_PLAYER_BALANCE,
    PROMOTION_COST,
    CommandAction,
    CommandEnvelope,
    CommandResult,
    DailyReport,
    GameSession,
)


class TestCommandAction:
    def test_enum_values(self) -> None:
        assert CommandAction.SET_PRICE.value == "set_price"
        assert CommandAction.BUY_BIKES.value == "buy_bikes"
        assert CommandAction.EXPAND_STATION.value == "expand_station"
        assert CommandAction.LAUNCH_PROMOTION.value == "launch_promotion"

    def test_enum_members(self) -> None:
        assert len(CommandAction) == 4


class TestCommandEnvelope:
    def test_creation(self) -> None:
        env = CommandEnvelope(
            session_id="sess_abc",
            command_id="cmd_123",
            action=CommandAction.SET_PRICE,
            payload={"station_id": "s1", "new_price_per_km": 2.0},
            timestamp=42,
        )
        assert env.session_id == "sess_abc"
        assert env.command_id == "cmd_123"
        assert env.action == CommandAction.SET_PRICE
        assert env.payload == {"station_id": "s1", "new_price_per_km": 2.0}
        assert env.timestamp == 42

    def test_frozen(self) -> None:
        env = CommandEnvelope(
            session_id="s", command_id="c", action=CommandAction.SET_PRICE,
            payload={}, timestamp=0,
        )
        with pytest.raises(AttributeError):
            env.session_id = "other"  # type: ignore[misc]


class TestCommandResult:
    def test_creation_defaults(self) -> None:
        r = CommandResult(
            command_id="cmd_1",
            action=CommandAction.BUY_BIKES,
            success=True,
            message="ok",
        )
        assert r.command_id == "cmd_1"
        assert r.success is True
        assert r.balance_change == 0.0
        assert r.new_balance == 0.0
        assert r.affected_station is None
        assert r.affected_count is None

    def test_creation_full(self) -> None:
        r = CommandResult(
            command_id="cmd_1",
            action=CommandAction.BUY_BIKES,
            success=True,
            message="bought 5 bikes",
            balance_change=-1000.0,
            new_balance=9000.0,
            affected_station="s1",
            affected_count=5,
        )
        assert r.balance_change == -1000.0
        assert r.new_balance == 9000.0
        assert r.affected_station == "s1"
        assert r.affected_count == 5

    def test_frozen(self) -> None:
        r = CommandResult(
            command_id="c", action=CommandAction.SET_PRICE,
            success=True, message="ok",
        )
        with pytest.raises(AttributeError):
            r.command_id = "other"  # type: ignore[misc]


class TestDailyReport:
    def test_creation_default_alert(self) -> None:
        r = DailyReport(
            day=1, revenue_today=1000.0, costs_today=800.0,
            profit_today=200.0, cumulative_balance=1200.0,
        )
        assert r.day == 1
        assert r.alert == ""

    def test_creation_with_alert(self) -> None:
        r = DailyReport(
            day=2, revenue_today=500.0, costs_today=500.0,
            profit_today=0.0, cumulative_balance=1200.0,
            alert="warning",
        )
        assert r.alert == "warning"


class TestGameSessionInit:
    def test_default_session_id(self) -> None:
        s = GameSession()
        assert s.session_id.startswith("session_")
        assert len(s.session_id) == 8 + 8

    def test_custom_session_id(self) -> None:
        s = GameSession(session_id="my_test_session")
        assert s.session_id == "my_test_session"

    def test_initial_balance(self) -> None:
        s = GameSession()
        assert s.player_balance == INITIAL_PLAYER_BALANCE

    def test_empty_queues(self) -> None:
        s = GameSession()
        assert s.command_queue == []
        assert s.command_history == []

    def test_empty_pending_effects(self) -> None:
        s = GameSession()
        assert s.pending_effects == {}


class TestGameSessionEnqueue:
    def test_returns_command_id(self) -> None:
        s = GameSession()
        cid = s.enqueue(CommandAction.SET_PRICE, {"station_id": "s1"}, tick=0)
        assert cid.startswith("cmd_")
        assert len(cid) == 16

    def test_adds_to_queue(self) -> None:
        s = GameSession()
        cid = s.enqueue(CommandAction.SET_PRICE, {"station_id": "s1"}, tick=5)
        assert len(s.command_queue) == 1
        env = s.command_queue[0]
        assert env.command_id == cid
        assert env.session_id == s.session_id
        assert env.action == CommandAction.SET_PRICE
        assert env.timestamp == 5

    def test_multiple_commands(self) -> None:
        s = GameSession()
        s.enqueue(CommandAction.SET_PRICE, {}, tick=1)
        s.enqueue(CommandAction.BUY_BIKES, {"count": 5}, tick=2)
        s.enqueue(CommandAction.EXPAND_STATION, {}, tick=3)
        assert len(s.command_queue) == 3
        assert s.command_queue[0].action == CommandAction.SET_PRICE
        assert s.command_queue[2].action == CommandAction.EXPAND_STATION


class TestGameSessionDrain:
    def test_returns_all_pending(self) -> None:
        s = GameSession()
        cid1 = s.enqueue(CommandAction.SET_PRICE, {}, tick=1)
        cid2 = s.enqueue(CommandAction.BUY_BIKES, {"count": 3}, tick=2)
        pending = s.drain_queue()
        assert len(pending) == 2
        assert pending[0].command_id == cid1
        assert pending[1].command_id == cid2

    def test_clears_queue(self) -> None:
        s = GameSession()
        s.enqueue(CommandAction.SET_PRICE, {}, tick=1)
        s.drain_queue()
        assert s.command_queue == []

    def test_empty_queue(self) -> None:
        s = GameSession()
        pending = s.drain_queue()
        assert pending == []


class TestGameSessionRecordResult:
    def test_appends_to_history(self) -> None:
        s = GameSession()
        r = CommandResult("c1", CommandAction.SET_PRICE, True, "ok")
        s.record_result(r)
        assert len(s.command_history) == 1
        assert s.command_history[0] is r

    def test_updates_balance_positive(self) -> None:
        s = GameSession()
        s.record_result(CommandResult(
            "c", CommandAction.SET_PRICE, True, "ok",
            balance_change=500.0, new_balance=10500.0,
        ))
        assert s.player_balance == 10500.0

    def test_updates_balance_negative(self) -> None:
        s = GameSession()
        s.record_result(CommandResult(
            "c", CommandAction.BUY_BIKES, True, "ok",
            balance_change=-1000.0, new_balance=9000.0,
        ))
        assert s.player_balance == 9000.0

    def test_multiple_records(self) -> None:
        s = GameSession()
        s.record_result(CommandResult("c1", CommandAction.SET_PRICE, True, "ok", balance_change=0.0, new_balance=10000.0))
        s.record_result(CommandResult("c2", CommandAction.BUY_BIKES, True, "ok", balance_change=-1000.0, new_balance=9000.0))
        assert s.player_balance == 9000.0
        assert len(s.command_history) == 2


class TestGameSessionFinancial:
    def test_can_afford_true(self) -> None:
        s = GameSession()
        assert s.can_afford(5000.0) is True

    def test_can_afford_exact(self) -> None:
        s = GameSession()
        assert s.can_afford(INITIAL_PLAYER_BALANCE) is True

    def test_can_afford_false(self) -> None:
        s = GameSession()
        assert s.can_afford(INITIAL_PLAYER_BALANCE + 1) is False

    def test_can_afford_epsilon_tolerance(self) -> None:
        s = GameSession()
        assert s.can_afford(9999.999) is True
        # epsilon = 0.001, so 10000.001 is within tolerance (10000 >= 10000.001-0.001)
        assert s.can_afford(10000.001) is True
        # beyond epsilon: 10000.002 - 0.001 = 10000.001 > 10000
        assert s.can_afford(10000.002) is False

    def test_deduct(self) -> None:
        s = GameSession()
        s.deduct(3000.0, "test")
        assert s.player_balance == 7000.0

    def test_deduct_multiple(self) -> None:
        s = GameSession()
        s.deduct(2000.0, "first")
        s.deduct(1000.0, "second")
        assert s.player_balance == 7000.0

    def test_deduct_negative_balance(self) -> None:
        s = GameSession()
        s.deduct(20000.0, "overspend")
        assert s.player_balance == -10000.0


class TestGameSessionToDict:
    def test_empty_session(self) -> None:
        s = GameSession(session_id="test_sid")
        d = s.to_dict()
        assert d["session_id"] == "test_sid"
        assert d["player_balance"] == INITIAL_PLAYER_BALANCE
        assert d["pending_commands"] == 0
        assert d["history_count"] == 0

    def test_with_pending(self) -> None:
        s = GameSession()
        s.enqueue(CommandAction.SET_PRICE, {}, tick=1)
        d = s.to_dict()
        assert d["pending_commands"] == 1

    def test_with_history(self) -> None:
        s = GameSession()
        s.record_result(CommandResult("c1", CommandAction.SET_PRICE, True, "ok"))
        d = s.to_dict()
        assert d["history_count"] == 1
        assert d["recent_results"][0]["command_id"] == "c1"
        assert d["recent_results"][0]["action"] == "set_price"

    def test_recent_results_limited(self) -> None:
        s = GameSession()
        for i in range(15):
            s.record_result(CommandResult(f"c{i}", CommandAction.SET_PRICE, True, "ok"))
        d = s.to_dict()
        assert len(d["recent_results"]) == 10

    def test_balance_rounded(self) -> None:
        s = GameSession()
        s.deduct(333.333, "test")
        d = s.to_dict()
        assert d["player_balance"] == round(10000.0 - 333.333, 2)


class TestGameSessionDailyReport:
    def test_none_by_default(self) -> None:
        s = GameSession()
        assert s.last_daily_report is None

    def test_set_and_get(self) -> None:
        s = GameSession()
        r = DailyReport(1, 1000.0, 800.0, 200.0, 10000.0)
        s.set_last_report(r)
        assert s.last_daily_report is not None
        assert s.last_daily_report.day == 1

    def test_set_none(self) -> None:
        s = GameSession()
        s.set_last_report(None)
        assert s.last_daily_report is None

    def test_overwrite(self) -> None:
        s = GameSession()
        s.set_last_report(DailyReport(1, 100, 80, 20, 10000.0))
        s.set_last_report(DailyReport(2, 200, 150, 50, 10200.0))
        assert s.last_daily_report.day == 2


class TestGameSessionConstants:
    def test_buy_bike_cost(self) -> None:
        assert BUY_BIKE_COST == 200.0

    def test_expand_station_cost(self) -> None:
        assert EXPAND_STATION_COST == 500.0

    def test_promotion_cost(self) -> None:
        assert PROMOTION_COST == 300.0

    def test_initial_balance(self) -> None:
        assert INITIAL_PLAYER_BALANCE == 10000.0


class TestGameSessionPendingEffects:
    def test_set_effect(self) -> None:
        s = GameSession()
        s.pending_effects["s1"] = {"type": "promotion", "remaining": 120}
        assert s.pending_effects["s1"]["type"] == "promotion"

    def test_clear(self) -> None:
        s = GameSession()
        s.pending_effects["s1"] = {"type": "promotion"}
        s.pending_effects.clear()
        assert s.pending_effects == {}
