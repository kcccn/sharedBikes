"""Event bus — lightweight pub/sub for decoupling tick events from consumers.

Usage::

    bus = EventBus.get_instance()

    # Subscribe
    bus.subscribe("tick", my_handler)
    bus.subscribe("tick", another_handler, key="ws_broadcast")

    # Publish
    bus.publish("tick", tick_events)

    # Unsubscribe
    bus.unsubscribe("tick", key="ws_broadcast")

Phase 5 consumers (WebSocket broadcaster, AchievementEngine) subscribe
to ``"tick"`` without any import-time coupling to ``SimulationEngine``.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Type alias for event handlers
TickEventHandler = Callable[["TickEvents"], None]
GenericHandler = Callable[[Any], None]


@dataclass
class Subscription:
    """A single subscription binding a handler to a topic."""

    topic: str
    handler: GenericHandler
    key: str | None = None
    _id: int = field(default=0, init=False, repr=False)


_counter = 0


def _next_id() -> int:
    global _counter
    _counter += 1
    return _counter


class EventBus:
    """Minimal synchronous event bus (singleton).

    Thread-safe for publish/subscribe. Handlers are invoked **in registration
    order** on the publisher's thread — consumers that need offloading (e.g.
    async WS broadcast) should queue internally and return immediately.
    """

    _instance: EventBus | None = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> EventBus:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._subscriptions: list[Subscription] = []
        return cls._instance

    # ── public API ───────────────────────────────────────────────

    def subscribe(
        self,
        topic: str,
        handler: GenericHandler,
        *,
        key: str | None = None,
    ) -> int:
        """Register a handler for *topic*. Returns a subscription ID for
        later removal. If *key* is provided, calling ``subscribe()`` again
        with the same key **replaces** the previous subscription."""
        if key is not None:
            self.unsubscribe(topic, key=key)
        sub = Subscription(topic=topic, handler=handler, key=key)
        sub._id = _next_id()
        with self._lock:
            self._subscriptions.append(sub)
        logger.debug("Subscribed to %s (key=%s, id=%d)", topic, key, sub._id)
        return sub._id

    def unsubscribe(self, topic: str, *, key: str | None = None) -> int:
        """Remove all subscriptions matching *topic* (and optionally *key*).
        Returns the number of subscriptions removed."""
        kept: list[Subscription] = []
        removed = 0
        with self._lock:
            for sub in self._subscriptions:
                if sub.topic == topic and (key is None or sub.key == key):
                    removed += 1
                else:
                    kept.append(sub)
            self._subscriptions = kept
        if removed:
            logger.debug("Unsubscribed %d handler(s) from %s (key=%s)", removed, topic, key)
        return removed

    def publish(self, topic: str, event: Any) -> None:
        """Synchronously invoke every handler registered for *topic*."""
        handlers: list[GenericHandler] = []
        with self._lock:
            for sub in self._subscriptions:
                if sub.topic == topic:
                    handlers.append(sub.handler)
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logger.exception("Handler %r failed on topic %s", handler, topic)

    def has_subscribers(self, topic: str) -> bool:
        """Check whether *topic* has any registered handlers."""
        with self._lock:
            return any(sub.topic == topic for sub in self._subscriptions)

    def clear(self) -> None:
        """Remove all subscriptions (useful in tests)."""
        with self._lock:
            self._subscriptions.clear()

    # ── test seam ────────────────────────────────────────────────

    @classmethod
    def reset_instance(cls) -> None:
        """Replace the singleton with a fresh instance (test helper)."""
        cls._instance = None
        _ = cls()


# ── re-export TickEvents for convenience ────────────────────────

from app.core.engine import TickEvents  # noqa: E402, F401
