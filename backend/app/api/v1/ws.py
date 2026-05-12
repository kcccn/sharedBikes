"""WebSocket endpoint — real-time simulation broadcast and bootstrap protocol.

Phase 5 WS bootstrap protocol (Option A):
1. On connect, server sends a one-shot ``bootstrap`` message containing all
   station metadata (id, name, x, y, capacity) so the frontend can
   initialise the abstract canvas without a separate REST call.
2. Server subscribes to ``EventBus`` "tick" events and forwards them as JSON.
3. On disconnect, the subscription is cleaned up.

Phase C extensions:
- Server receives ``command`` messages from the client, validates and enqueues
  them to the GameSession via EngineManager.
- Tick messages include ``balance`` and optional ``daily_report`` fields.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.event_bus import EventBus, TickEvents
from app.services.engine_manager import EngineManager

ws_router = APIRouter()


def _serialize_station(station: Any) -> dict[str, Any]:
    """Serialize a City Station dataclass to a WS-friendly dict."""
    return {
        "station_id": station.station_id,
        "name": station.name,
        "x": station.position.x,
        "y": station.position.y,
        "capacity": station.capacity,
    }


def _serialize_tick(
    event: TickEvents,
    demand_factors: dict[str, float] | None = None,
    balance: float | None = None,
    daily_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Serialize a TickEvents dataclass to a WS tick message payload.

    Args:
        event: The tick event to serialize.
        demand_factors: Optional per-station demand factors [0.0, 1.0]
            from ``StationStatsTracker.get_demand_factors()`` (Phase 6 P2).
        balance: Optional player balance from GameSession (Phase C).
        daily_report: Optional daily report dict (Phase C).
    """
    trips = [
        {
            "from_station": t.from_station,
            "to_station": t.to_station,
            "distance_km": t.distance_km,
        }
        for t in event.trips
    ]
    payload: dict[str, Any] = {
        "type": "tick",
        "tick": event.tick,
        "time": event.time_of_day,
        "station_inventory": dict(event.station_inventory),
        "weather": event.weather,
        "trips": trips,
        "dispatch_movements": [
            {"from": f, "to": t, "count": c}
            for f, t, c in event.dispatch_movements
        ],
    }
    if demand_factors is not None:
        payload["demand_factors"] = demand_factors

    # Phase C: player-facing data
    if balance is not None:
        payload["balance"] = round(balance, 2)
    if daily_report is not None:
        payload["daily_report"] = daily_report

    return payload


@ws_router.websocket("/ws")
async def simulation_ws(websocket: WebSocket) -> None:
    """WebSocket handler: bootstrap → tick stream ← command inbox.

    Protocol
    --------
    1. Server accepts the connection.
    2. Server sends ``{"type": "bootstrap", "stations": [...]}`` with all
       station metadata (one-shot).
    3. Server subscribes to ``EventBus`` "tick" events and forwards them as
       ``{"type": "tick", ...}`` messages (includes balance + daily_report
       from GameSession).
    4. Server listens for incoming ``{"type": "command", ...}`` messages,
       validates them, enqueues to GameSession, and replies with
       ``{"type": "command_result", ...}``.
    5. Client disconnect → server unsubscribes from the EventBus.
    """
    await websocket.accept()

    # ── Bootstrap: station metadata (one-shot) ───────────────────
    mgr = EngineManager()
    city = mgr.engine.city
    stations = [_serialize_station(s) for s in city.stations.values()]

    # Include initial session balance in bootstrap
    bootstrap_msg: dict[str, Any] = {
        "type": "bootstrap",
        "stations": stations,
        "balance": round(mgr.last_tick_balance, 2),
    }
    await websocket.send_json(bootstrap_msg)

    # ── Sync→async bridge via asyncio.Queue ──────────────────────
    queue: asyncio.Queue[TickEvents] = asyncio.Queue()
    _closed = False

    def tick_handler(event: TickEvents) -> None:
        """Sync handler invoked on the publisher's thread."""
        if not _closed:
            queue.put_nowait(event)

    # Unique subscription key per connection to support multiple WS clients
    conn_key = f"ws_{id(websocket)}"
    bus = EventBus()
    bus.subscribe("tick", tick_handler, key=conn_key)

    async def _reader() -> None:
        """Continuously read incoming WebSocket messages (commands)."""
        try:
            while not _closed:
                raw = await websocket.receive_text()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                if not isinstance(msg, dict) or msg.get("type") != "command":
                    continue

                # ── Handle player command ──
                action = msg.get("action", "")
                payload = msg.get("payload", {})
                command_id = msg.get("command_id", "")

                if not action or not isinstance(payload, dict):
                    await _send_error(websocket, command_id, "无效的指令格式")
                    continue

                # Enqueue via EngineManager
                mgr = EngineManager()
                result_id = mgr.enqueue_command(action, payload, mgr.engine.tick)

                if result_id is None:
                    # Validation failed — get the detailed error
                    from app.services.command_handler import CommandHandler
                    from app.services.game_session import CommandAction

                    try:
                        cmd_action = CommandAction(action)
                        validation = CommandHandler.validate(
                            cmd_action, payload, mgr.session, mgr.engine
                        )
                        msg_text = validation.message
                    except (ValueError, Exception):
                        msg_text = f"指令校验失败: {action}"

                    await _send_error(websocket, command_id or result_id or "unknown", msg_text)
                else:
                    await websocket.send_json({
                        "type": "command_result",
                        "command_id": command_id or result_id,
                        "success": True,
                        "message": f"指令已提交: {action}",
                        "balance_change": 0,
                        "new_balance": round(mgr.session.player_balance, 2),
                    })
        except (WebSocketDisconnect, RuntimeError):
            pass  # normal disconnect
        except Exception:
            pass  # suppress any unexpected errors during cleanup

    async def _send_error(
        ws: WebSocket,
        cmd_id: str,
        msg: str,
    ) -> None:
        """Send a command error result."""
        try:
            mgr = EngineManager()
            await ws.send_json({
                "type": "command_result",
                "command_id": cmd_id,
                "success": False,
                "message": msg,
                "balance_change": 0,
                "new_balance": round(mgr.session.player_balance, 2),
            })
        except Exception:
            pass

    # ── Start concurrent reader for incoming commands ────────────
    reader_task = asyncio.create_task(_reader())

    try:
        # ── Forward tick events ──────────────────────────────────
        while True:
            event: TickEvents = await queue.get()
            # Inject demand_factors from StationStatsTracker (Phase 6 P2)
            factors = mgr.station_stats_tracker.get_demand_factors()
            # Phase C: balance + daily report
            balance = mgr.last_tick_balance
            daily_report = mgr.last_daily_report_dict
            payload = _serialize_tick(
                event,
                demand_factors=factors,
                balance=balance,
                daily_report=daily_report,
            )
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        pass  # normal disconnect
    except Exception:
        pass  # suppress any unexpected errors during cleanup
    finally:
        _closed = True
        bus.unsubscribe("tick", key=conn_key)
        reader_task.cancel()
        try:
            await reader_task
        except (asyncio.CancelledError, Exception):
            pass
