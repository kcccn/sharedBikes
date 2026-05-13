"""Dedicated unit tests for CommandHandler (Phase C).

Covers validate() and execute() for all four command types:
SET_PRICE, BUY_BIKES, EXPAND_STATION, LAUNCH_PROMOTION.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.core.city import City, Coord, Station
from app.services.command_handler import CommandHandler
from app.services.game_session import (
    BUY_BIKE_COST,
    EXPAND_STATION_COST,
    INITIAL_PLAYER_BALANCE,
    PROMOTION_COST,
    CommandAction,
    CommandResult,
    GameSession,
)


# ── fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def session() -> GameSession:
    return GameSession(session_id="test_session")


@pytest.fixture
def stations() -> dict[str, Station]:
    return {
        "s1": Station(station_id="s1", position=Coord(0, 0), capacity=30),
        "s2": Station(station_id="s2", position=Coord(10, 10), capacity=30),
    }


@pytest.fixture
def engine(stations: dict[str, Station]) -> MagicMock:
    eng = MagicMock()
    city = City(nodes={}, edges={}, stations=stations, zones={})
    eng.city = city
    eng._station_price_overrides = {}
    eng._station_capacity_overrides = {}
    eng.fleet = MagicMock()
    eng.environment = MagicMock()
    eng.environment.events = {}
    return eng


# ======================================================================
# CommandHandler.validate()
# ======================================================================


class TestValidateSetPrice:
    def test_valid(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.SET_PRICE,
            {"station_id": "s1", "new_price_per_km": 2.5},
            session,
            engine,
        )
        assert result.success is True
        assert "校验通过" in result.message

    def test_empty_station_id(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.SET_PRICE,
            {"station_id": "", "new_price_per_km": 2.0},
            session,
            engine,
        )
        assert result.success is False
        assert "station_id" in result.message

    def test_nonexistent_station(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.SET_PRICE,
            {"station_id": "nonexistent", "new_price_per_km": 2.0},
            session,
            engine,
        )
        assert result.success is False
        assert "不存在" in result.message

    def test_price_too_low(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.SET_PRICE,
            {"station_id": "s1", "new_price_per_km": 0.3},
            session,
            engine,
        )
        assert result.success is False
        assert "定价过低" in result.message

    def test_price_too_high(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.SET_PRICE,
            {"station_id": "s1", "new_price_per_km": 15.0},
            session,
            engine,
        )
        assert result.success is False
        assert "定价过高" in result.message

    def test_boundary_min_valid(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.SET_PRICE,
            {"station_id": "s1", "new_price_per_km": 0.5},
            session,
            engine,
        )
        assert result.success is True

    def test_boundary_max_valid(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.SET_PRICE,
            {"station_id": "s1", "new_price_per_km": 10.0},
            session,
            engine,
        )
        assert result.success is True


class TestValidateBuyBikes:
    def test_valid(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.BUY_BIKES,
            {"count": 5},
            session,
            engine,
        )
        assert result.success is True

    def test_count_not_int(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.BUY_BIKES,
            {"count": "five"},
            session,
            engine,
        )
        assert result.success is False
        assert "无效" in result.message

    def test_count_zero(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.BUY_BIKES,
            {"count": 0},
            session,
            engine,
        )
        assert result.success is False

    def test_count_negative(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.BUY_BIKES,
            {"count": -3},
            session,
            engine,
        )
        assert result.success is False

    def test_count_exceeds_limit(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.BUY_BIKES,
            {"count": 101},
            session,
            engine,
        )
        assert result.success is False
        assert "上限" in result.message

    def test_count_max_valid(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.BUY_BIKES,
            {"count": 100},
            session,
            engine,
        )
        assert result.success is True

    def test_insufficient_funds(self, session: GameSession, engine: MagicMock) -> None:
        """100 bikes = 20000 cost, but balance is 10000."""
        result = CommandHandler.validate(
            CommandAction.BUY_BIKES,
            {"count": 100},
            session,
            engine,
        )
        assert result.success is False
        assert "余额不足" in result.message

    def test_exact_funds(self, session: GameSession, engine: MagicMock) -> None:
        """50 bikes = 10000, exactly matching balance."""
        result = CommandHandler.validate(
            CommandAction.BUY_BIKES,
            {"count": 50},
            session,
            engine,
        )
        assert result.success is True


class TestValidateExpandStation:
    def test_valid(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.EXPAND_STATION,
            {"station_id": "s1", "additional_capacity": 5},
            session,
            engine,
        )
        assert result.success is True

    def test_empty_station_id(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.EXPAND_STATION,
            {"station_id": "", "additional_capacity": 5},
            session,
            engine,
        )
        assert result.success is False
        assert "station_id" in result.message

    def test_nonexistent_station(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.EXPAND_STATION,
            {"station_id": "nope", "additional_capacity": 5},
            session,
            engine,
        )
        assert result.success is False
        assert "不存在" in result.message

    def test_capacity_not_int(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.EXPAND_STATION,
            {"station_id": "s1", "additional_capacity": "ten"},
            session,
            engine,
        )
        assert result.success is False
        assert "无效" in result.message

    def test_capacity_zero(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.EXPAND_STATION,
            {"station_id": "s1", "additional_capacity": 0},
            session,
            engine,
        )
        assert result.success is False

    def test_capacity_negative(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.EXPAND_STATION,
            {"station_id": "s1", "additional_capacity": -1},
            session,
            engine,
        )
        assert result.success is False

    def test_capacity_exceeds_limit(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.EXPAND_STATION,
            {"station_id": "s1", "additional_capacity": 51},
            session,
            engine,
        )
        assert result.success is False
        assert "上限" in result.message

    def test_capacity_max_valid(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.EXPAND_STATION,
            {"station_id": "s1", "additional_capacity": 50},
            session,
            engine,
        )
        assert result.success is True

    def test_insufficient_funds(self, session: GameSession, engine: MagicMock) -> None:
        """21 * 500 = 10500 > 10000"""
        result = CommandHandler.validate(
            CommandAction.EXPAND_STATION,
            {"station_id": "s1", "additional_capacity": 21},
            session,
            engine,
        )
        assert result.success is False
        assert "余额不足" in result.message


class TestValidateLaunchPromotion:
    def test_valid(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.LAUNCH_PROMOTION,
            {"station_id": "s1", "duration_ticks": 120, "demand_boost": 2.0},
            session,
            engine,
        )
        assert result.success is True

    def test_empty_station_id(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.LAUNCH_PROMOTION,
            {"station_id": "", "duration_ticks": 120, "demand_boost": 2.0},
            session,
            engine,
        )
        assert result.success is False
        assert "station_id" in result.message

    def test_nonexistent_station(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.LAUNCH_PROMOTION,
            {"station_id": "fake", "duration_ticks": 120, "demand_boost": 2.0},
            session,
            engine,
        )
        assert result.success is False
        assert "不存在" in result.message

    def test_duration_too_short(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.LAUNCH_PROMOTION,
            {"station_id": "s1", "duration_ticks": 5, "demand_boost": 2.0},
            session,
            engine,
        )
        assert result.success is False
        assert "持续时间" in result.message

    def test_duration_too_long(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.LAUNCH_PROMOTION,
            {"station_id": "s1", "duration_ticks": 1500, "demand_boost": 2.0},
            session,
            engine,
        )
        assert result.success is False
        assert "持续时间" in result.message

    def test_duration_min_valid(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.LAUNCH_PROMOTION,
            {"station_id": "s1", "duration_ticks": 10, "demand_boost": 2.0},
            session,
            engine,
        )
        assert result.success is True

    def test_duration_max_valid(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.LAUNCH_PROMOTION,
            {"station_id": "s1", "duration_ticks": 1440, "demand_boost": 2.0},
            session,
            engine,
        )
        assert result.success is True

    def test_boost_too_low(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.LAUNCH_PROMOTION,
            {"station_id": "s1", "duration_ticks": 120, "demand_boost": 0.5},
            session,
            engine,
        )
        assert result.success is False
        assert "需求倍率" in result.message

    def test_boost_too_high(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.LAUNCH_PROMOTION,
            {"station_id": "s1", "duration_ticks": 120, "demand_boost": 6.0},
            session,
            engine,
        )
        assert result.success is False
        assert "需求倍率" in result.message

    def test_boost_min_valid(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.LAUNCH_PROMOTION,
            {"station_id": "s1", "duration_ticks": 120, "demand_boost": 1.0},
            session,
            engine,
        )
        assert result.success is True

    def test_boost_max_valid(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            CommandAction.LAUNCH_PROMOTION,
            {"station_id": "s1", "duration_ticks": 120, "demand_boost": 5.0},
            session,
            engine,
        )
        assert result.success is True

    def test_insufficient_funds(self, session: GameSession, engine: MagicMock) -> None:
        """Cost for 1440 ticks = 300 + 144*50 = 7500. Use poor session with 2000."""
        poor = GameSession(session_id="poor")
        poor.deduct(8000.0, "make poor")
        result = CommandHandler.validate(
            CommandAction.LAUNCH_PROMOTION,
            {"station_id": "s1", "duration_ticks": 1440, "demand_boost": 2.0},
            poor,
            engine,
        )
        assert result.success is False
        assert "余额不足" in result.message


class TestValidateUnknownAction:
    def test_unknown_action(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.validate(
            "unknown_action",  # type: ignore[arg-type]
            {},
            session,
            engine,
        )
        assert result.success is False
        assert "未知指令类型" in result.message


# ======================================================================
# CommandHandler.execute()
# ======================================================================


class TestExecuteSetPrice:
    def test_sets_price_override(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.execute(
            CommandAction.SET_PRICE,
            {"station_id": "s1", "new_price_per_km": 3.0},
            session,
            engine,
            command_id="cmd_set",
            tick=10,
        )
        assert result.success is True
        assert engine._station_price_overrides["s1"] == 3.0
        assert result.affected_station == "s1"
        assert result.balance_change == 0.0

    def test_overwrites_existing(self, session: GameSession, engine: MagicMock) -> None:
        engine._station_price_overrides["s1"] = 2.0
        result = CommandHandler.execute(
            CommandAction.SET_PRICE,
            {"station_id": "s1", "new_price_per_km": 5.0},
            session,
            engine,
            command_id="cmd_set2",
            tick=20,
        )
        assert engine._station_price_overrides["s1"] == 5.0
        assert result.success is True


class TestExecuteBuyBikes:
    def test_creates_bikes_and_deducts(
        self, session: GameSession, engine: MagicMock,
    ) -> None:
        result = CommandHandler.execute(
            CommandAction.BUY_BIKES,
            {"count": 3},
            session,
            engine,
            command_id="cmd_buy",
            tick=10,
        )
        assert result.success is True
        assert result.affected_count == 3
        expected_cost = 3 * BUY_BIKE_COST
        assert result.balance_change == -expected_cost
        assert result.new_balance == INITIAL_PLAYER_BALANCE - expected_cost
        assert engine.fleet.add_bike.call_count == 3
        engine.append_ledger.assert_called_once()

    def test_single_bike(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.execute(
            CommandAction.BUY_BIKES,
            {"count": 1},
            session,
            engine,
            command_id="cmd_buy1",
            tick=5,
        )
        assert result.success is True
        assert result.affected_count == 1
        assert result.balance_change == -BUY_BIKE_COST
        engine.fleet.add_bike.assert_called_once()


class TestExecuteExpandStation:
    def test_increases_capacity(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.execute(
            CommandAction.EXPAND_STATION,
            {"station_id": "s1", "additional_capacity": 10},
            session,
            engine,
            command_id="cmd_exp",
            tick=15,
        )
        assert result.success is True
        assert engine._station_capacity_overrides["s1"] == 10
        assert result.affected_station == "s1"
        assert result.affected_count == 10
        expected_cost = 10 * EXPAND_STATION_COST
        assert result.balance_change == -expected_cost
        engine.append_ledger.assert_called_once()

    def test_accumulates_with_existing(
        self, session: GameSession, engine: MagicMock,
    ) -> None:
        engine._station_capacity_overrides["s1"] = 5
        CommandHandler.execute(
            CommandAction.EXPAND_STATION,
            {"station_id": "s1", "additional_capacity": 10},
            session,
            engine,
            command_id="cmd_exp2",
            tick=20,
        )
        assert engine._station_capacity_overrides["s1"] == 15


class TestExecuteLaunchPromotion:
    def test_creates_special_event(
        self, session: GameSession, engine: MagicMock,
    ) -> None:
        result = CommandHandler.execute(
            CommandAction.LAUNCH_PROMOTION,
            {"station_id": "s1", "duration_ticks": 120, "demand_boost": 2.0},
            session,
            engine,
            command_id="cmd_promo",
            tick=30,
        )
        assert result.success is True
        assert result.affected_station == "s1"
        assert len(engine.environment.events) == 1
        event_id = list(engine.environment.events.keys())[0]
        assert "promo_cmd_promo" in event_id
        event = engine.environment.events[event_id]
        assert event.station_id == "s1"
        assert event.demand_multiplier == 2.0
        assert event.duration_ticks == 120

    def test_tracks_pending_effects(
        self, session: GameSession, engine: MagicMock,
    ) -> None:
        CommandHandler.execute(
            CommandAction.LAUNCH_PROMOTION,
            {"station_id": "s2", "duration_ticks": 60, "demand_boost": 1.5},
            session,
            engine,
            command_id="cmd_promo2",
            tick=40,
        )
        assert "s2" in session.pending_effects
        effect = session.pending_effects["s2"]
        assert effect["type"] == "promotion"
        assert effect["remaining_ticks"] == 60
        assert effect["boost"] == 1.5

    def test_computes_total_cost(
        self, session: GameSession, engine: MagicMock,
    ) -> None:
        result = CommandHandler.execute(
            CommandAction.LAUNCH_PROMOTION,
            {"station_id": "s1", "duration_ticks": 120, "demand_boost": 2.0},
            session,
            engine,
            command_id="cmd_promo3",
            tick=50,
        )
        expected_cost = PROMOTION_COST + int(120 / 10) * 50  # 300 + 600 = 900
        assert result.balance_change == -expected_cost
        engine.append_ledger.assert_called_once()


class TestExecuteUnknownAction:
    def test_unknown_action(self, session: GameSession, engine: MagicMock) -> None:
        result = CommandHandler.execute(
            "unknown_action",  # type: ignore[arg-type]
            {},
            session,
            engine,
            command_id="cmd_unknown",
            tick=0,
        )
        assert result.success is False
        assert "未知指令类型" in result.message
