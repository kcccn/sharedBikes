"""GameSession — player-facing session managing command queues and player balance.

Phase C: GameSession wraps a simulation session with player interaction:
- Holds player_balance (separate from the engine's ledger balance)
- Maintains command_queue (pending) and command_history (executed)
- Tracks pending_effects for active promotions
- Not a Core layer model — lives in Service layer

The EngineManager owns the GameSession instance and drains the command
queue before each advance() call.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CommandAction(str, Enum):
    """Supported player command actions."""

    SET_PRICE = "set_price"
    BUY_BIKES = "buy_bikes"
    EXPAND_STATION = "expand_station"
    LAUNCH_PROMOTION = "launch_promotion"


@dataclass(frozen=True)
class CommandEnvelope:
    """Wraps a raw player command with session metadata.

    ``command_id`` is server-generated for idempotent WS confirmation.
    """

    session_id: str
    command_id: str
    action: CommandAction
    payload: dict[str, Any]
    timestamp: int  # engine tick when received


@dataclass(frozen=True)
class CommandResult:
    """Result returned after validating and executing a player command."""

    command_id: str
    action: CommandAction
    success: bool
    message: str
    balance_change: float = 0.0
    new_balance: float = 0.0
    affected_station: str | None = None
    affected_count: int | None = None


@dataclass
class DailyReport:
    """Extended daily report with player-facing fields."""

    day: int
    revenue_today: float
    costs_today: float
    profit_today: float
    cumulative_balance: float
    alert: str = ""


# ── Cost constants for player actions ───────────────────────────

BUY_BIKE_COST = 200.0          # cost per bike purchased
EXPAND_STATION_COST = 500.0     # cost per +1 capacity
PROMOTION_COST = 300.0          # base cost per promotion launch
INITIAL_PLAYER_BALANCE = 10000.0  # starting capital


class GameSession:
    """Player session bound to a simulation engine.

    Thread-safe notes: EngineManager serialises access, so no locks
    are needed within GameSession itself.
    """

    def __init__(self, session_id: str | None = None) -> None:
        self.session_id: str = session_id or f"session_{uuid.uuid4().hex[:8]}"
        self.player_balance: float = INITIAL_PLAYER_BALANCE
        self.command_queue: list[CommandEnvelope] = []
        self.command_history: list[CommandResult] = []
        self.pending_effects: dict[str, Any] = {}  # station_id -> effect info

    # ── command queue management ─────────────────────────────────

    def enqueue(
        self,
        action: CommandAction,
        payload: dict[str, Any],
        tick: int,
    ) -> str:
        """Add a command to the pending queue.

        Returns the server-generated command_id.
        """
        command_id = f"cmd_{uuid.uuid4().hex[:12]}"
        envelope = CommandEnvelope(
            session_id=self.session_id,
            command_id=command_id,
            action=action,
            payload=payload,
            timestamp=tick,
        )
        self.command_queue.append(envelope)
        return command_id

    def drain_queue(self) -> list[CommandEnvelope]:
        """Extract and return all pending commands (clears the queue)."""
        pending = list(self.command_queue)
        self.command_queue.clear()
        return pending

    def record_result(self, result: CommandResult) -> None:
        """Append an executed command result to history."""
        self.command_history.append(result)
        self.player_balance += result.balance_change  # balance_change is net delta

    # ── financial helpers ───────────────────────────────────────

    def can_afford(self, cost: float) -> bool:
        """Check if player has sufficient balance."""
        return self.player_balance >= cost - 0.001  # small epsilon for float safety

    def deduct(self, amount: float, reason: str) -> None:
        """Deduct from player balance (recorded via CommandResult)."""
        self.player_balance -= amount

    # ── session queries ─────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Return a snapshot of the session for API responses."""
        return {
            "session_id": self.session_id,
            "player_balance": round(self.player_balance, 2),
            "pending_commands": len(self.command_queue),
            "history_count": len(self.command_history),
            "recent_results": [
                {
                    "command_id": r.command_id,
                    "action": r.action.value,
                    "success": r.success,
                    "message": r.message,
                    "balance_change": r.balance_change,
                    "new_balance": r.new_balance,
                }
                for r in self.command_history[-10:]
            ],
        }

    @property
    def last_daily_report(self) -> DailyReport | None:
        """Return the most recent daily report from history (extracted from tick data)."""
        # This is populated externally by EngineManager from engine.daily_reports
        if hasattr(self, "_last_report") and self._last_report is not None:
            return self._last_report  # type: ignore[has-type]
        return None

    def set_last_report(self, report: DailyReport | None) -> None:
        """Store the latest daily report (called by EngineManager after advance)."""
        self._last_report = report  # type: ignore[has-type]
