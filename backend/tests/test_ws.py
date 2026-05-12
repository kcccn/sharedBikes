"""Tests for the WebSocket bootstrap protocol and EventBus integration.

Strategy
--------
We test the WS handler through ``TestClient`` (Starlette's async test
client). Because the EventBus is a singleton, we reset it before each
test to ensure isolation.

Scenarios
---------
- ``test_bootstrap_contains_all_stations`` — the first message on connect
  is a ``bootstrap`` payload with every station's metadata.
- ``test_tick_events_forwarded`` — after bootstrap, publishing a
  ``TickEvents`` via EventBus produces a ``tick`` message on the wire.
- ``test_disconnect_unsubscribes`` — when the client disconnects, the
  subscription key is removed from EventBus.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.event_bus import EventBus, TickEvents
from app.main import app


# ── fixtures ─────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_event_bus():
    """Reset the EventBus singleton before each test."""
    EventBus.reset_instance()
    yield


@pytest.fixture
def client():
    """Return a TestClient bound to the FastAPI app.

    The WebSocket endpoint is at ``/api/v1/ws``.
    """
    return TestClient(app)


# ── helpers ──────────────────────────────────────────────────────


def _collect_messages(ws, n: int, timeout: float = 3.0) -> list[dict[str, Any]]:
    """Receive *n* JSON messages from *ws*, decoding each."""
    messages: list[dict[str, Any]] = []
    for _ in range(n):
        raw = ws.receive_text()
        messages.append(json.loads(raw))
    return messages


# ── tests ────────────────────────────────────────────────────────


class TestWebSocketBootstrap:
    """WS bootstrap message contains station metadata."""

    def test_bootstrap_contains_all_stations(self, client: TestClient):
        """The first message on connect is a ``bootstrap`` message with
        all stations from the live city model."""
        with client.websocket_connect("/api/v1/ws") as ws:
            msg = json.loads(ws.receive_text())

        assert msg["type"] == "bootstrap"
        assert "stations" in msg
        assert len(msg["stations"]) > 0

        # Each station must have all required fields (abstract Coord: x, y)
        for station in msg["stations"]:
            assert "station_id" in station
            assert "name" in station
            assert "x" in station
            assert "y" in station
            assert "capacity" in station

    def test_bootstrap_fields_are_correct_types(
        self, client: TestClient
    ):
        """Field types are correct for frontend consumption."""
        with client.websocket_connect("/api/v1/ws") as ws:
            msg = json.loads(ws.receive_text())

        station = msg["stations"][0]
        assert isinstance(station["station_id"], str)
        assert isinstance(station["name"], str)
        assert isinstance(station["x"], (int, float))
        assert isinstance(station["y"], (int, float))
        assert isinstance(station["capacity"], int)


class TestWebSocketTickForwarding:
    """Tick events published on EventBus are forwarded to the WS client."""

    def test_tick_event_forwarded(self, client: TestClient):
        """Publishing a TickEvents via EventBus produces a tick message."""
        with client.websocket_connect("/api/v1/ws") as ws:
            # Consume bootstrap
            ws.receive_text()

            # Publish a tick event
            bus = EventBus.get_instance()
            event = TickEvents(
                tick=42,
                time_of_day="08:15",
                station_inventory={"station_A": 5, "station_B": 3},
                weather="CLEAR",
            )
            bus.publish("tick", event)

            # Read the forwarded message
            msg = json.loads(ws.receive_text())

        assert msg["type"] == "tick"
        assert msg["tick"] == 42
        assert msg["time"] == "08:15"
        assert msg["station_inventory"] == {"station_A": 5, "station_B": 3}
        assert msg["weather"] == "CLEAR"

    def test_tick_includes_trips_and_movements(
        self, client: TestClient
    ):
        """Tick message includes trips and dispatch_movements."""
        with client.websocket_connect("/api/v1/ws") as ws:
            ws.receive_text()  # consume bootstrap

            bus = EventBus.get_instance()
            event = TickEvents(
                tick=1,
                time_of_day="00:01",
                trips=[],  # empty is fine for now
                dispatch_movements=[("A", "B", 3)],
            )
            bus.publish("tick", event)

            msg = json.loads(ws.receive_text())

        assert "trips" in msg
        assert "dispatch_movements" in msg
        assert msg["dispatch_movements"] == [
            {"from": "A", "to": "B", "count": 3}
        ]

    def test_multiple_ticks_forwarded_in_order(
        self, client: TestClient
    ):
        """Multiple tick events arrive in publication order."""
        with client.websocket_connect("/api/v1/ws") as ws:
            ws.receive_text()  # bootstrap

            bus = EventBus.get_instance()
            for i in range(3):
                bus.publish("tick", TickEvents(tick=i, time_of_day=f"00:0{i}"))

            messages = _collect_messages(ws, 3)

        assert [m["tick"] for m in messages] == [0, 1, 2]


class TestWebSocketDisconnect:
    """Clean teardown on disconnect."""

    def test_disconnect_unsubscribes(self, client: TestClient):
        """After disconnect, the ``ws_*`` subscription key is removed."""
        with client.websocket_connect("/api/v1/ws") as ws:
            ws.receive_text()  # bootstrap
            # Let the context manager close the connection

        bus = EventBus.get_instance()
        assert not bus.has_subscribers("tick")

    def test_reconnect_sends_fresh_bootstrap(
        self, client: TestClient
    ):
        """A second connection receives its own bootstrap message."""
        # First connection
        with client.websocket_connect("/api/v1/ws") as ws:
            msg1 = json.loads(ws.receive_text())

        # Second connection
        with client.websocket_connect("/api/v1/ws") as ws:
            msg2 = json.loads(ws.receive_text())

        assert msg1["type"] == "bootstrap"
        assert msg2["type"] == "bootstrap"
        # Both should have the same stations (same city)
        assert len(msg1["stations"]) == len(msg2["stations"])
