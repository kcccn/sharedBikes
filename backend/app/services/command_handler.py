"""CommandHandler — validates and executes player commands against the engine.

Phase C: Each player command type has a validate() and execute() method.
All commands consume player funds and are recorded via the engine's ledger.

Key design:
- validate() is pure — no state mutations
- execute() mutates the engine/game state and returns a CommandResult
- Costs are deducted from GameSession.player_balance
- All financial impacts are also written to the engine's Ledger
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from app.core.finance import CostCategory, LedgerEntry, RevenueCategory
from app.services.game_session import (
    BUY_BIKE_COST,
    EXPAND_STATION_COST,
    PROMOTION_COST,
    CommandAction,
    CommandResult,
    GameSession,
)

if TYPE_CHECKING:
    from app.core.engine import SimulationEngine
    from app.core.weather import SpecialEvent

logger = logging.getLogger(__name__)


class CommandHandler:
    """Validates and executes player commands.

    Stateless — all state is held in GameSession and SimulationEngine.
    """

    @staticmethod
    def validate(
        action: CommandAction,
        payload: dict[str, Any],
        session: GameSession,
        engine: SimulationEngine,
    ) -> CommandResult:
        """Validate a command without mutating state.

        Returns a CommandResult with success=False and a message if invalid.
        Returns success=True (no balance change) if valid.
        """
        # Generic checks
        if action == CommandAction.SET_PRICE:
            return CommandHandler._validate_set_price(payload, engine)
        elif action == CommandAction.BUY_BIKES:
            return CommandHandler._validate_buy_bikes(payload, session, engine)
        elif action == CommandAction.EXPAND_STATION:
            return CommandHandler._validate_expand_station(payload, session, engine)
        elif action == CommandAction.LAUNCH_PROMOTION:
            return CommandHandler._validate_launch_promotion(payload, session, engine)
        else:
            return CommandResult(
                command_id="",
                action=action,
                success=False,
                message=f"未知指令类型: {action}",
            )

    @staticmethod
    def execute(
        action: CommandAction,
        payload: dict[str, Any],
        session: GameSession,
        engine: SimulationEngine,
        command_id: str,
        tick: int,
    ) -> CommandResult:
        """Execute a validated command and return the result.

        Caller must ensure validate() passed before calling execute().
        Mutates engine state and session.player_balance.
        """
        if action == CommandAction.SET_PRICE:
            return CommandHandler._execute_set_price(payload, session, engine, command_id)
        elif action == CommandAction.BUY_BIKES:
            return CommandHandler._execute_buy_bikes(payload, session, engine, command_id, tick)
        elif action == CommandAction.EXPAND_STATION:
            return CommandHandler._execute_expand_station(payload, session, engine, command_id, tick)
        elif action == CommandAction.LAUNCH_PROMOTION:
            return CommandHandler._execute_launch_promotion(payload, session, engine, command_id, tick)
        else:
            return CommandResult(
                command_id=command_id,
                action=action,
                success=False,
                message=f"未知指令类型: {action}",
            )

    # ── SetPrice ─────────────────────────────────────────────────

    @staticmethod
    def _validate_set_price(
        payload: dict[str, Any],
        engine: SimulationEngine,
    ) -> CommandResult:
        station_id = payload.get("station_id", "")
        new_price = payload.get("new_price_per_km", 0.0)

        if not station_id:
            return _error("station_id 不能为空")
        if station_id not in engine.city.stations:
            return _error(f"站点 {station_id} 不存在")
        if new_price < 0.5:
            return _error(f"定价过低 ({new_price})，最低 ¥0.5")
        if new_price > 10.0:
            return _error(f"定价过高 ({new_price})，最高 ¥10.0")

        return _ok()

    @staticmethod
    def _execute_set_price(
        payload: dict[str, Any],
        session: GameSession,
        engine: SimulationEngine,
        command_id: str,
    ) -> CommandResult:
        station_id = payload["station_id"]
        new_price = payload["new_price_per_km"]

        # Apply per-station price override via engine's pricing tier override system
        engine._station_price_overrides[station_id] = new_price  # type: ignore[attr-defined]

        old_balance = session.player_balance
        return CommandResult(
            command_id=command_id,
            action=CommandAction.SET_PRICE,
            success=True,
            message=f"{station_id} 定价已调整为 ¥{new_price:.1f}/km",
            balance_change=0.0,
            new_balance=old_balance,
            affected_station=station_id,
        )

    # ── BuyBikes ─────────────────────────────────────────────────

    @staticmethod
    def _validate_buy_bikes(
        payload: dict[str, Any],
        session: GameSession,
        engine: SimulationEngine,
    ) -> CommandResult:
        count = payload.get("count", 0)
        if not isinstance(count, int) or count < 1:
            return _error(f"购买数量无效: {count}")
        if count > 100:
            return _error(f"单次购买上限 100 辆，请求 {count} 辆")
        total_cost = count * BUY_BIKE_COST
        if not session.can_afford(total_cost):
            return _error(
                f"余额不足: 需要 ¥{total_cost:.0f}（{count} 辆 × ¥{BUY_BIKE_COST:.0f}），"
                f"当前余额 ¥{session.player_balance:.2f}"
            )
        return _ok()

    @staticmethod
    def _execute_buy_bikes(
        payload: dict[str, Any],
        session: GameSession,
        engine: SimulationEngine,
        command_id: str,
        tick: int,
    ) -> CommandResult:
        count = payload["count"]
        total_cost = count * BUY_BIKE_COST

        # Create new bikes and add to fleet
        from app.core.fleet import Bike

        new_bikes: list[str] = []
        for i in range(count):
            bike_id = f"bike_player_{tick}_{i}"
            bike = Bike(bike_id=bike_id, station_id=None)
            engine.fleet.add_bike(bike)
            new_bikes.append(bike_id)

        # Deduct from player balance (handled by _drain_commands → record_result)
        old_balance = session.player_balance

        # Record in engine's ledger as a cost entry
        from app.core.finance import LedgerEntry, CostCategory

        entry = LedgerEntry(
            tick=tick,
            entry_id=f"{command_id}_cost",
            category=CostCategory.BIKE_MAINTENANCE,
            amount=-total_cost,
            description=f"玩家购买 {count} 辆单车 (command {command_id})",
        )
        engine.append_ledger([entry])

        return CommandResult(
            command_id=command_id,
            action=CommandAction.BUY_BIKES,
            success=True,
            message=f"成功购买 {count} 辆单车，花费 ¥{total_cost:.0f}",
            balance_change=-total_cost,
            new_balance=old_balance - total_cost,
            affected_count=count,
        )

    # ── ExpandStation ────────────────────────────────────────────

    @staticmethod
    def _validate_expand_station(
        payload: dict[str, Any],
        session: GameSession,
        engine: SimulationEngine,
    ) -> CommandResult:
        station_id = payload.get("station_id", "")
        add_cap = payload.get("additional_capacity", 0)

        if not station_id:
            return _error("station_id 不能为空")
        if station_id not in engine.city.stations:
            return _error(f"站点 {station_id} 不存在")
        if not isinstance(add_cap, int) or add_cap < 1:
            return _error(f"扩容数量无效: {add_cap}")
        if add_cap > 50:
            return _error(f"单次扩容上限 50，请求 {add_cap}")
        total_cost = add_cap * EXPAND_STATION_COST
        if not session.can_afford(total_cost):
            return _error(
                f"余额不足: 需要 ¥{total_cost:.0f}（+{add_cap} 容量 × ¥{EXPAND_STATION_COST:.0f}），"
                f"当前余额 ¥{session.player_balance:.2f}"
            )
        return _ok()

    @staticmethod
    def _execute_expand_station(
        payload: dict[str, Any],
        session: GameSession,
        engine: SimulationEngine,
        command_id: str,
        tick: int,
    ) -> CommandResult:
        station_id = payload["station_id"]
        add_cap = payload["additional_capacity"]
        total_cost = add_cap * EXPAND_STATION_COST

        # Apply capacity override
        current_override = engine._station_capacity_overrides.get(station_id, 0)  # type: ignore[attr-defined]
        engine._station_capacity_overrides[station_id] = current_override + add_cap  # type: ignore[attr-defined]

        old_balance = session.player_balance

        # Ledger entry
        entry = LedgerEntry(
            tick=tick,
            entry_id=f"{command_id}_cost",
            category=CostCategory.STATION_LEASE,
            amount=-total_cost,
            description=f"玩家扩容 {station_id} +{add_cap} (command {command_id})",
        )
        engine.append_ledger([entry])

        return CommandResult(
            command_id=command_id,
            action=CommandAction.EXPAND_STATION,
            success=True,
            message=f"{station_id} 扩容成功 (+{add_cap} 容量)，花费 ¥{total_cost:.0f}",
            balance_change=-total_cost,
            new_balance=old_balance - total_cost,
            affected_station=station_id,
            affected_count=add_cap,
        )

    # ── LaunchPromotion ──────────────────────────────────────────

    @staticmethod
    def _validate_launch_promotion(
        payload: dict[str, Any],
        session: GameSession,
        engine: SimulationEngine,
    ) -> CommandResult:
        station_id = payload.get("station_id", "")
        duration = payload.get("duration_ticks", 0)
        boost = payload.get("demand_boost", 0.0)

        if not station_id:
            return _error("station_id 不能为空")
        if station_id not in engine.city.stations:
            return _error(f"站点 {station_id} 不存在")
        if not isinstance(duration, int) or duration < 10:
            return _error(f"促销持续时间无效: {duration}（最少 10 tick）")
        if duration > 1440:
            return _error(f"促销持续时间过长: {duration}（最多 1440 tick = 1 天）")
        if not isinstance(boost, (int, float)) or boost < 1.0:
            return _error(f"需求倍率无效: {boost}（最少 1.0x）")
        if boost > 5.0:
            return _error(f"需求倍率过高: {boost}（最多 5.0x）")
        total_cost = PROMOTION_COST + int(duration / 10) * 50
        if not session.can_afford(total_cost):
            return _error(
                f"余额不足: 需要 ¥{total_cost:.0f}，当前余额 ¥{session.player_balance:.2f}"
            )
        return _ok()

    @staticmethod
    def _execute_launch_promotion(
        payload: dict[str, Any],
        session: GameSession,
        engine: SimulationEngine,
        command_id: str,
        tick: int,
    ) -> CommandResult:
        station_id = payload["station_id"]
        duration = payload["duration_ticks"]
        boost = payload["demand_boost"]
        total_cost = PROMOTION_COST + int(duration / 10) * 50

        # Register a SpecialEvent in the engine's environment
        from app.core.weather import SpecialEvent

        event_id = f"promo_{command_id}"
        special_event = SpecialEvent(
            event_id=event_id,
            name=f"促销: {station_id}",
            station_id=station_id,
            radius_km=0.5,
            demand_multiplier=boost,
            duration_ticks=duration,
            remaining_ticks=duration,
        )
        engine.environment.events[event_id] = special_event

        # Track in session's pending effects
        session.pending_effects[station_id] = {
            "type": "promotion",
            "event_id": event_id,
            "remaining_ticks": duration,
            "boost": boost,
        }

        old_balance = session.player_balance
        session.deduct(total_cost, reason=f"促销 {station_id} ({duration}tick ×{boost})")

        # Ledger entry
        entry = LedgerEntry(
            tick=tick,
            entry_id=f"{command_id}_cost",
            category=CostCategory.OVERHEAD,
            amount=-total_cost,
            description=f"玩家促销 {station_id} {duration}tick ×{boost} (command {command_id})",
        )
        engine.append_ledger([entry])

        return CommandResult(
            command_id=command_id,
            action=CommandAction.LAUNCH_PROMOTION,
            success=True,
            message=f"{station_id} 促销启动: {duration}tick ×{boost:.1f} 需求倍率，花费 ¥{total_cost:.0f}",
            balance_change=-total_cost,
            new_balance=old_balance - total_cost,
            affected_station=station_id,
        )


def _ok() -> CommandResult:
    """Return a no-op valid result."""
    return CommandResult(
        command_id="",
        action=CommandAction.SET_PRICE,
        success=True,
        message="校验通过",
    )


def _error(msg: str) -> CommandResult:
    """Return a validation error result."""
    return CommandResult(
        command_id="",
        action=CommandAction.SET_PRICE,
        success=False,
        message=msg,
    )
