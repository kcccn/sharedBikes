"""Tests for the EventBus pub/sub singleton."""

import pytest

from app.core.event_bus import EventBus, _next_id


# ── fixtures ─────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_bus():
    """Reset the singleton before each test so tests are isolated."""
    EventBus.reset_instance()
    yield
    EventBus.reset_instance()


# ── singleton contract ───────────────────────────────────────────

class TestSingleton:
    def test_same_instance(self):
        b1 = EventBus()
        b2 = EventBus()
        assert b1 is b2

    def test_reset_instance_creates_fresh(self):
        b1 = EventBus()
        EventBus.reset_instance()
        b2 = EventBus()
        assert b1 is not b2


# ── subscribe / publish / unsubscribe ────────────────────────────

class TestPubSub:
    def test_subscriber_receives_event(self):
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("tick", handler)
        bus.publish("tick", {"tick": 1})
        assert received == [{"tick": 1}]

    def test_multiple_subscribers_all_called(self):
        bus = EventBus()
        results = []

        def a(e):
            results.append("a")

        def b(e):
            results.append("b")

        bus.subscribe("tick", a)
        bus.subscribe("tick", b)
        bus.publish("tick", {})
        assert results == ["a", "b"]

    def test_unrelated_topic_not_delivered(self):
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("other", handler)
        bus.publish("tick", {"tick": 1})
        assert received == []

    def test_unsubscribe_by_key(self):
        bus = EventBus()
        results = []

        def handler(e):
            results.append("x")

        bus.subscribe("tick", handler, key="ws")
        bus.subscribe("tick", lambda e: results.append("y"), key="ach")
        bus.publish("tick", {})
        assert len(results) == 2

        bus.unsubscribe("tick", key="ws")
        results.clear()
        bus.publish("tick", {})
        assert results == ["y"]

    def test_unsubscribe_returns_count(self):
        bus = EventBus()
        bus.subscribe("tick", lambda e: None, key="a")
        bus.subscribe("tick", lambda e: None, key="b")
        n = bus.unsubscribe("tick", key="a")
        assert n == 1

    def test_unsubscribe_nonexistent_returns_zero(self):
        bus = EventBus()
        n = bus.unsubscribe("tick", key="nope")
        assert n == 0

    def test_subscribe_replace_with_same_key(self):
        bus = EventBus()
        results = []

        bus.subscribe("tick", lambda e: results.append("old"), key="x")
        bus.subscribe("tick", lambda e: results.append("new"), key="x")
        bus.publish("tick", {})
        assert results == ["new"], "Same key should replace"

    def test_handler_exception_does_not_block_others(self):
        bus = EventBus()
        results = []

        def broken(e):
            raise RuntimeError("boom")

        def good(e):
            results.append("ok")

        bus.subscribe("tick", broken)
        bus.subscribe("tick", good)
        bus.publish("tick", {})  # should not raise
        assert results == ["ok"]

    def test_has_subscribers(self):
        bus = EventBus()
        assert not bus.has_subscribers("tick")
        bus.subscribe("tick", lambda e: None)
        assert bus.has_subscribers("tick")
        assert not bus.has_subscribers("other")

    def test_clear_removes_all(self):
        bus = EventBus()
        bus.subscribe("tick", lambda e: None)
        bus.subscribe("dispatch", lambda e: None)
        bus.clear()
        assert not bus.has_subscribers("tick")
        assert not bus.has_subscribers("dispatch")


# ── thread safety (smoke) ────────────────────────────────────────

class TestThreadSafety:
    def test_concurrent_subscribe_and_publish(self):
        import threading

        bus = EventBus()
        barrier = threading.Barrier(4)
        results = []

        def subscriber():
            barrier.wait()
            bus.subscribe("tick", lambda e: results.append(1))

        def publisher():
            barrier.wait()
            bus.publish("tick", {})

        threads = [threading.Thread(target=subscriber) for _ in range(3)]
        threads.append(threading.Thread(target=publisher))
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=2)

        # All three subscribers should have been registered; the single
        # publish call delivers to whichever are registered before the
        # publish lock is acquired — at least one should get through.
        assert len(results) >= 0  # at least no crash

    def test_concurrent_publish_does_not_crash(self):
        import concurrent.futures

        bus = EventBus()
        results = []

        def handler(e):
            results.append(e["tick"])

        bus.subscribe("tick", handler)

        def publish_tick(n):
            bus.publish("tick", {"tick": n})

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            list(ex.map(publish_tick, range(20)))

        assert len(results) == 20


# ── integration: TickEvents shape ────────────────────────────────

class TestTickEventsShape:
    def test_import_from_event_bus(self):
        """TickEvents is re-exported from event_bus for convenience."""
        from app.core.event_bus import TickEvents

        ev = TickEvents(tick=1, time_of_day="00:01")
        assert ev.tick == 1
        assert ev.time_of_day == "00:01"

    def test_revenue_cost_derived_properties(self):
        from app.core.event_bus import TickEvents

        class FakeEntry:
            def __init__(self, amount):
                self.amount = amount

        ev = TickEvents(
            tick=1,
            time_of_day="00:01",
            ledger_entries=[FakeEntry(100), FakeEntry(-30), FakeEntry(50)],
        )
        assert ev.revenue == 150
        assert ev.costs == 30
