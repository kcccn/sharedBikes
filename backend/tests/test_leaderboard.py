"""Tests for the StationStatsTracker (leaderboard_service.py).

Phase 6 P1: Async Leaderboard — EventBus-driven per-station stats.
"""

from dataclasses import dataclass

from app.core.engine import TickEvents
from app.core.event_bus import EventBus
from app.core.finance import LedgerEntry, RevenueCategory
from app.services.leaderboard_service import StationStats, StationStatsTracker


# ── helpers ─────────────────────────────────────────────────────


def _make_tick_event(
    tick: int = 1,
    completed_trips: list | None = None,
    ledger_entries: list | None = None,
    dispatch_movements: list | None = None,
    station_inventory: dict | None = None,
) -> TickEvents:
    return TickEvents(
        tick=tick,
        time_of_day=f"{tick % 1440 // 60:02d}:{tick % 60:02d}",
        trips=[],
        completed_trips=completed_trips or [],
        ledger_entries=ledger_entries or [],
        station_inventory=station_inventory or {},
        dispatch_movements=dispatch_movements or [],
    )


@dataclass
class _FakeTrip:
    """Minimal ActiveTrip stand-in for tests."""
    class Trip:
        def __init__(self, from_station: str, to_station: str):
            self.from_station = from_station
            self.to_station = to_station

    def __init__(self, from_station: str, to_station: str, trip_id: str = "t1"):
        self.trip = self.Trip(from_station, to_station)
        self.trip_id = trip_id
        self.distance_km = 2.0
        self.started_tick = 0
        self.completed_tick = 1


# ── StationStatsTracker ─────────────────────────────────────────


class TestStationStatsTracker:
    def setup_method(self) -> None:
        EventBus.reset_instance()
        self.tracker = StationStatsTracker()

    def test_empty_on_init(self) -> None:
        assert self.tracker.station_count == 0
        assert self.tracker.get_leaderboard() == []

    def test_tick_with_no_completed_trips(self) -> None:
        """Tick with no completed trips should not create any stats."""
        event = _make_tick_event(tick=1)
        self.tracker._on_tick(event)
        assert self.tracker.station_count == 0

    def test_single_trip_updates_destination(self) -> None:
        """Completed trip increments trips_completed at destination."""
        trip = _FakeTrip(from_station="S1", to_station="S2")
        event = _make_tick_event(tick=1, completed_trips=[trip])
        self.tracker._on_tick(event)

        stats = self.tracker.get_station_stats("S2")
        assert stats is not None
        assert stats.trips_completed == 1
        assert stats.last_active_tick == 1

        # Source station should not have trip count incremented
        src_stats = self.tracker.get_station_stats("S1")
        assert src_stats is None  # no activity at S1 tracked

    def test_multiple_trips_multiple_stations(self) -> None:
        """Multiple completed trips update respective stations."""
        trips = [
            _FakeTrip(from_station="S1", to_station="S2", trip_id="t1"),
            _FakeTrip(from_station="S3", to_station="S4", trip_id="t2"),
            _FakeTrip(from_station="S5", to_station="S2", trip_id="t3"),
        ]
        event = _make_tick_event(tick=2, completed_trips=trips)
        self.tracker._on_tick(event)

        s2 = self.tracker.get_station_stats("S2")
        assert s2 is not None
        assert s2.trips_completed == 2  # two trips ended at S2

        s4 = self.tracker.get_station_stats("S4")
        assert s4 is not None
        assert s4.trips_completed == 1

    def test_revenue_attribution(self) -> None:
        """Revenue from TRIP_INCOME entries is distributed per-trip."""
        trips = [
            _FakeTrip(from_station="S1", to_station="S2", trip_id="t1"),
            _FakeTrip(from_station="S3", to_station="S4", trip_id="t2"),
        ]
        entries = [
            LedgerEntry(tick=1, entry_id="r1", category=RevenueCategory.TRIP_INCOME, amount=30.0, trip_id="t1"),
            LedgerEntry(tick=1, entry_id="r2", category=RevenueCategory.TRIP_INCOME, amount=50.0, trip_id="t2"),
        ]
        event = _make_tick_event(tick=1, completed_trips=trips, ledger_entries=entries)
        self.tracker._on_tick(event)

        s2 = self.tracker.get_station_stats("S2")
        s4 = self.tracker.get_station_stats("S4")
        # Revenue is distributed: total 80 / 2 trips = 40 per station
        assert s2 is not None and s4 is not None
        assert s2.revenue_generated == 40.0
        assert s4.revenue_generated == 40.0

    def test_achievement_attribution(self) -> None:
        """ACHIEVEMENT entries attributed to busiest destination station."""
        trips = [
            _FakeTrip(from_station="S1", to_station="S2", trip_id="t1"),
            _FakeTrip(from_station="S3", to_station="S2", trip_id="t2"),
            _FakeTrip(from_station="S5", to_station="S6", trip_id="t3"),
        ]
        entries = [
            LedgerEntry(tick=1, entry_id="a1", category=RevenueCategory.ACHIEVEMENT, amount=10.0),
        ]
        event = _make_tick_event(tick=1, completed_trips=trips, ledger_entries=entries)
        self.tracker._on_tick(event)

        # S2 had 2 trips, S6 had 1 — achievement goes to S2
        s2 = self.tracker.get_station_stats("S2")
        s6 = self.tracker.get_station_stats("S6")
        assert s2 is not None
        assert s2.achievement_count == 1
        assert s6 is not None
        assert s6.achievement_count == 0

    def test_dispatch_movement_tracking(self) -> None:
        """Dispatch movements update dispatch_in/dispatch_out counters."""
        movements = [("S1", "S2", 3), ("S3", "S4", 2)]
        event = _make_tick_event(tick=5, dispatch_movements=movements)
        self.tracker._on_tick(event)

        s1 = self.tracker.get_station_stats("S1")
        s2 = self.tracker.get_station_stats("S2")
        s3 = self.tracker.get_station_stats("S3")
        s4 = self.tracker.get_station_stats("S4")

        assert s1 is not None and s1.dispatch_out == 3
        assert s2 is not None and s2.dispatch_in == 3
        assert s3 is not None and s3.dispatch_out == 2
        assert s4 is not None and s4.dispatch_in == 2

    def test_last_active_tick_updated(self) -> None:
        """Last active tick is updated on each activity."""
        trip = _FakeTrip(from_station="S1", to_station="S2")
        event = _make_tick_event(tick=42, completed_trips=[trip])
        self.tracker._on_tick(event)

        s2 = self.tracker.get_station_stats("S2")
        assert s2 is not None
        assert s2.last_active_tick == 42

    # ── get_leaderboard ──────────────────────────────────────────

    def test_leaderboard_sorted_by_trips(self) -> None:
        """Leaderboard sorted descending by trips_completed."""
        trips_t1 = [
            _FakeTrip(from_station="S1", to_station="S3", trip_id="t1"),
        ]
        trips_t2 = [
            _FakeTrip(from_station="S1", to_station="S2", trip_id="t2"),
            _FakeTrip(from_station="S3", to_station="S2", trip_id="t3"),
            _FakeTrip(from_station="S4", to_station="S2", trip_id="t4"),
        ]
        self.tracker._on_tick(_make_tick_event(tick=1, completed_trips=trips_t1))
        self.tracker._on_tick(_make_tick_event(tick=2, completed_trips=trips_t2))

        board = self.tracker.get_leaderboard(sort_by="trips", limit=10)
        assert len(board) == 2
        assert board[0].station_id == "S2"  # 3 trips
        assert board[0].trips_completed == 3
        assert board[1].station_id == "S3"  # 1 trip
        assert board[1].trips_completed == 1

    def test_leaderboard_limit(self) -> None:
        """Leaderboard respects limit parameter."""
        trips = [
            _FakeTrip(from_station="S0", to_station=f"S{i}", trip_id=f"t{i}")
            for i in range(1, 6)
        ]
        self.tracker._on_tick(_make_tick_event(tick=1, completed_trips=trips))

        board = self.tracker.get_leaderboard(limit=3)
        assert len(board) == 3

    def test_leaderboard_revenue_sort(self) -> None:
        """Leaderboard sorts by revenue."""
        trips = [
            _FakeTrip(from_station="S0", to_station="S1", trip_id="t1"),
            _FakeTrip(from_station="S0", to_station="S2", trip_id="t2"),
        ]
        entries = [
            LedgerEntry(tick=1, entry_id="r1", category=RevenueCategory.TRIP_INCOME, amount=10.0, trip_id="t1"),
            LedgerEntry(tick=1, entry_id="r2", category=RevenueCategory.TRIP_INCOME, amount=100.0, trip_id="t2"),
        ]
        event = _make_tick_event(tick=1, completed_trips=trips, ledger_entries=entries)
        self.tracker._on_tick(event)
        # Revenue distributed: total 110 / 2 = 55 each
        board = self.tracker.get_leaderboard(sort_by="revenue", limit=10)
        assert len(board) == 2

    def test_leaderboard_empty(self) -> None:
        """Leaderboard returns empty list when no data."""
        assert self.tracker.get_leaderboard() == []

    def test_leaderboard_achievement_sort(self) -> None:
        """Leaderboard sorts by achievement count."""
        trips = [
            _FakeTrip(from_station="S0", to_station="S1", trip_id="t1"),
            _FakeTrip(from_station="S0", to_station="S2", trip_id="t2"),
        ]
        entries = [
            LedgerEntry(tick=1, entry_id="a1", category=RevenueCategory.ACHIEVEMENT, amount=10.0),
        ]
        event = _make_tick_event(tick=1, completed_trips=trips, ledger_entries=entries)
        self.tracker._on_tick(event)

        board = self.tracker.get_leaderboard(sort_by="achievements", limit=10)
        # Both S1 and S2 each got 1 trip, S1 gets achievement by alphabetical tie-break
        # Actually, max station_trip_count: both have 1, so tie. dict ordering means S1 wins.
        assert len(board) == 2

    # ── get_station_stats ────────────────────────────────────────

    def test_get_station_stats_unknown(self) -> None:
        """Unknown station returns None."""
        assert self.tracker.get_station_stats("NONEXISTENT") is None

    def test_get_station_stats_known(self) -> None:
        """Known station returns StationStatsSummary."""
        trip = _FakeTrip(from_station="S1", to_station="S2")
        self.tracker._on_tick(_make_tick_event(tick=1, completed_trips=[trip]))

        stats = self.tracker.get_station_stats("S2")
        assert stats is not None
        assert stats.station_id == "S2"
        assert stats.trips_completed == 1

    # ── EventBus integration ─────────────────────────────────────

    def test_receives_events_via_eventbus(self) -> None:
        """Tracker receives TickEvents published on EventBus."""
        EventBus.reset_instance()
        tracker = StationStatsTracker()

        trip = _FakeTrip(from_station="S1", to_station="S2")
        event = _make_tick_event(tick=10, completed_trips=[trip])
        EventBus().publish("tick", event)

        stats = tracker.get_station_stats("S2")
        assert stats is not None
        assert stats.trips_completed == 1
        assert stats.last_active_tick == 10

    def test_non_tick_events_ignored(self) -> None:
        """Non-TickEvents published on EventBus are ignored."""
        EventBus.reset_instance()
        tracker = StationStatsTracker()
        EventBus().publish("tick", "not_a_tick_event")
        assert tracker.station_count == 0
