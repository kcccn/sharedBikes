"""Leaderboard service — StationStatsTracker for async station-level stats.

Phase 6 P1: Pure backend module that subscribes to EventBus ``"tick"``
events (sibling consumer alongside AchievementEngine) and maintains
per-station in-memory counters. REST API queries these counters on
demand — no DB, no WebSocket push.

Architecture::

    EventBus.publish("tick", TickEvents)
             │
             ├──► AchievementEngine._on_tick()
             │
             └──► StationStatsTracker._on_tick()    ← this module
                          │
                          ▼
                  per-station counters (in-memory)
                          │
                          ▼
                  GET /leaderboard/stations?sort_by=trips&limit=10
                  GET /leaderboard/stations/{station_id}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.event_bus import EventBus
from app.core.finance import RevenueCategory


@dataclass
class StationStats:
    """Per-station runtime statistics accumulated across ticks."""

    station_id: str
    trips_completed: int = 0          # cumulative completed trips ending at this station
    revenue_generated: float = 0.0    # cumulative revenue from trips ending at this station
    profit_contributed: float = 0.0   # cumulative profit from trips ending at this station
    achievement_count: int = 0        # achievement unlocks attributed to this station
    dispatch_in: int = 0              # cumulative bikes dispatched TO this station
    dispatch_out: int = 0             # cumulative bikes dispatched FROM this station
    last_active_tick: int = 0         # last tick with activity at this station


# ── public DTOs (matches backend/app/models/schemas.py) ─────────


@dataclass
class LeaderboardEntry:
    """A single row in the station leaderboard."""

    station_id: str
    trips_completed: int
    revenue_generated: float
    profit_contributed: float
    achievement_count: int
    dispatch_in: int
    dispatch_out: int
    last_active_tick: int


@dataclass
class StationStatsSummary:
    """Detailed stats for a single station."""

    station_id: str
    trips_completed: int
    revenue_generated: float
    profit_contributed: float
    achievement_count: int
    dispatch_in: int
    dispatch_out: int
    last_active_tick: int


class StationStatsTracker:
    """Subscribe to EventBus tick events and maintain per-station stats.

    Uses ``TickEvents.completed_trips`` (ActiveTrip objects with from_station
    and to_station) and ``TickEvents.ledger_entries`` to attribute trips,
    revenue, and achievements to individual stations.

    Engine restart (reset → reinit) creates a fresh tracker, so counters
    are automatically reset — no explicit clear needed.
    """

    def __init__(self) -> None:
        self._stats: dict[str, StationStats] = {}
        self._total_revenue_this_tick: float = 0.0
        self._total_completed_this_tick: int = 0

        # Subscribe to EventBus tick events
        EventBus().subscribe("tick", self._on_tick, key="leaderboard")

    # ── tick handler ────────────────────────────────────────────

    def _on_tick(self, event: Any) -> None:
        """EventBus handler — update per-station counters from TickEvents."""
        from app.core.engine import TickEvents

        if not isinstance(event, TickEvents):
            return

        tick = event.tick
        completed_trips = event.completed_trips
        ledger_entries = event.ledger_entries
        dispatch_movements = event.dispatch_movements

        # --- Attribute completed trips to destination stations ---
        for at in completed_trips:
            sid = at.trip.to_station
            stats = self._stats.setdefault(sid, StationStats(station_id=sid))
            stats.trips_completed += 1
            if tick > stats.last_active_tick:
                stats.last_active_tick = tick

        # --- Attribute revenue entries to stations ---
        # Revenue entries don't carry station_id directly, but we can
        # approximate by distributing revenue proportionally among
        # stations that received completed trips this tick.
        revenue_entries = [
            e for e in ledger_entries
            if isinstance(e.category, RevenueCategory)
            and e.category == RevenueCategory.TRIP_INCOME
        ]
        total_revenue = sum(e.amount for e in revenue_entries)
        total_completed = len(completed_trips)

        if total_completed > 0 and total_revenue > 0:
            revenue_per_trip = total_revenue / total_completed
            for at in completed_trips:
                sid = at.trip.to_station
                stats = self._stats.setdefault(sid, StationStats(station_id=sid))
                stats.revenue_generated += revenue_per_trip
                stats.profit_contributed += revenue_per_trip  # TODO(#136): profit needs cost attribution — currently approximated as revenue

        # --- Attribute achievement entries to stations ---
        # ACHIEVEMENT entries don't have station_id, so we count them
        # globally and attribute to the most-active station.
        achievement_entries = [
            e for e in ledger_entries
            if isinstance(e.category, RevenueCategory)
            and e.category == RevenueCategory.ACHIEVEMENT
        ]
        if achievement_entries and completed_trips:
            # Attribute achievement to the station with the most completed trips this tick
            station_trip_count: dict[str, int] = {}
            for at in completed_trips:
                sid = at.trip.to_station
                station_trip_count[sid] = station_trip_count.get(sid, 0) + 1
            if station_trip_count:
                busiest_sid = max(station_trip_count, key=station_trip_count.get)
                stats = self._stats.setdefault(busiest_sid, StationStats(station_id=busiest_sid))
                stats.achievement_count += len(achievement_entries)

        # --- Attribute dispatch movements ---
        for from_sid, to_sid, count in dispatch_movements:
            # Outgoing
            out_stats = self._stats.setdefault(from_sid, StationStats(station_id=from_sid))
            out_stats.dispatch_out += count
            if tick > out_stats.last_active_tick:
                out_stats.last_active_tick = tick
            # Incoming
            in_stats = self._stats.setdefault(to_sid, StationStats(station_id=to_sid))
            in_stats.dispatch_in += count
            if tick > in_stats.last_active_tick:
                in_stats.last_active_tick = tick

    # ── query methods ───────────────────────────────────────────

    def get_leaderboard(
        self,
        sort_by: Literal["trips", "revenue", "profit", "achievements"] = "trips",
        limit: int = 10,
    ) -> list[LeaderboardEntry]:
        """Return top-N stations sorted by the given metric.

        Args:
            sort_by: Sort dimension — ``"trips"``, ``"revenue"``,
                     ``"profit"``, or ``"achievements"``.
            limit: Maximum number of entries to return (default 10).

        Returns:
            List of ``LeaderboardEntry`` sorted descending by *sort_by*.
        """
        entries = [
            LeaderboardEntry(
                station_id=s.station_id,
                trips_completed=s.trips_completed,
                revenue_generated=s.revenue_generated,
                profit_contributed=s.profit_contributed,
                achievement_count=s.achievement_count,
                dispatch_in=s.dispatch_in,
                dispatch_out=s.dispatch_out,
                last_active_tick=s.last_active_tick,
            )
            for s in self._stats.values()
        ]

        # Sort by the requested metric (descending)
        if sort_by == "trips":
            entries.sort(key=lambda e: e.trips_completed, reverse=True)
        elif sort_by == "revenue":
            entries.sort(key=lambda e: e.revenue_generated, reverse=True)
        elif sort_by == "profit":
            entries.sort(key=lambda e: e.profit_contributed, reverse=True)
        elif sort_by == "achievements":
            entries.sort(key=lambda e: e.achievement_count, reverse=True)
        else:
            entries.sort(key=lambda e: e.trips_completed, reverse=True)

        return entries[:limit]

    def get_station_stats(self, station_id: str) -> StationStatsSummary | None:
        """Return detailed stats for a single station, or None if unknown."""
        stats = self._stats.get(station_id)
        if stats is None:
            return None
        return StationStatsSummary(
            station_id=stats.station_id,
            trips_completed=stats.trips_completed,
            revenue_generated=stats.revenue_generated,
            profit_contributed=stats.profit_contributed,
            achievement_count=stats.achievement_count,
            dispatch_in=stats.dispatch_in,
            dispatch_out=stats.dispatch_out,
            last_active_tick=stats.last_active_tick,
        )

    @property
    def station_count(self) -> int:
        """Number of stations with recorded activity."""
        return len(self._stats)
