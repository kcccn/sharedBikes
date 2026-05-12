"""WebSocket endpoint — real-time simulation broadcast and bootstrap protocol.

Phase 5 WS bootstrap protocol (Option A):
1. On connect, server sends a one-shot ``bootstrap`` message containing all
   station metadata (id, name, lat, lng, capacity) so the frontend can
   initialise Leaflet markers without a separate REST call.
2. Server subscribes to ``EventBus`` "tick" events and forwards them as JSON.
3. On disconnect, the subscription is cleaned up.

Sync→async bridge
------------------
``EventBus`` invokes handlers synchronously on the publisher's thread.
Each WS connection maintains an ``asyncio.Queue``; a sync ``put_nowait``
handler bridges into the async world, and a concurrent reader task sends
queued events over the WebSocket.
"""

from __future__ import annotations

import asyncio
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
        "lat": station.position.lat,
        "lng": station.position.lng,
        "capacity": station.capacity,
    }


def _serialize_tick(
    event: TickEvents,
    demand_factors: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Serialize a TickEvents dataclass to a WS tick message payload.

    Args:
        event: The tick event to serialize.
        demand_factors: Optional per-station demand factors [0.0, 1.0]
            from ``StationStatsTracker.get_demand_factors()`` (Phase 6 P2).
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
    return payload


@ws_router.websocket("/ws")
async def simulation_ws(websocket: WebSocket) -> None:
    """WebSocket handler: bootstrap → tick stream.

    Protocol
    --------
    1. Server accepts the connection.
    2. Server sends ``{"type": "bootstrap", "stations": [...]}`` with all
       station metadata (one-shot).
    3. Server subscribes to ``EventBus`` "tick" events and forwards them as
       ``{"type": "tick", ...}`` messages.
    4. Client disconnect → server unsubscribes from the EventBus.
    """
    await websocket.accept()

    # ── Bootstrap: station metadata (one-shot) ───────────────────
    mgr = EngineManager()
    city = mgr.engine.city
    stations = [_serialize_station(s) for s in city.stations.values()]
    await websocket.send_json({"type": "bootstrap", "stations": stations})

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

    try:
        # ── Forward tick events ──────────────────────────────────
        while True:
            event: TickEvents = await queue.get()
            payload = _serialize_tick(event)
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        pass  # normal disconnect
    except Exception:
        pass  # suppress any unexpected errors during cleanup
    finally:
        _closed = True
        bus.unsubscribe("tick", key=conn_key)
