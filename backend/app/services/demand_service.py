"""Demand generation service."""

from __future__ import annotations


class DemandService:
    """Generates NPC trip demand based on time, weather, and events.

    Phase 2: Implement real commuter-tide demand model.
    """

    def generate_trips(self, tick: int, time_of_day: str) -> list[dict]:
        """Stub — returns empty trip list.

        TODO(phase-2): generate trips based on real demand model.
        """
        return []
