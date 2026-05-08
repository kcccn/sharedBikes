"""Tests for the cost engine (costing.py)."""

from app.core.costing import CostEngine, CostParams
from app.core.finance import CostCategory


# ── per_tick — first tick of day (tick_in_day == 0) ─────────────


def test_first_tick_daily_costs() -> None:
    """At tick_in_day == 0, daily costs (lease + maintenance) are posted."""
    engine = CostEngine()
    entries = engine.per_tick(tick=1440, tick_in_day=0, total_bikes=100, total_stations=10)
    assert len(entries) == 2  # maintenance + lease

    # Maintenance: 100 bikes × ¥0.5 = ¥50
    maint = [e for e in entries if e.category == CostCategory.BIKE_MAINTENANCE]
    assert len(maint) == 1
    assert maint[0].amount == -50.0

    # Lease: 10 stations × ¥10.0 = ¥100
    lease = [e for e in entries if e.category == CostCategory.STATION_LEASE]
    assert len(lease) == 1
    assert lease[0].amount == -100.0


def test_first_tick_zero_bikes_no_cost() -> None:
    """No bikes → no maintenance cost."""
    engine = CostEngine()
    entries = engine.per_tick(tick=1440, tick_in_day=0, total_bikes=0, total_stations=5)
    maint = [e for e in entries if e.category == CostCategory.BIKE_MAINTENANCE]
    assert len(maint) == 0


def test_first_tick_zero_stations_no_cost() -> None:
    """No stations → no lease cost."""
    engine = CostEngine()
    entries = engine.per_tick(tick=1440, tick_in_day=0, total_bikes=100, total_stations=0)
    lease = [e for e in entries if e.category == CostCategory.STATION_LEASE]
    assert len(lease) == 0


# ── per_tick — non-first tick of day (tick_in_day != 0) ─────────


def test_mid_tick_no_daily_costs() -> None:
    """At tick_in_day != 0, no daily costs are posted."""
    engine = CostEngine()
    entries = engine.per_tick(tick=1, tick_in_day=1, total_bikes=100, total_stations=10)
    assert len(entries) == 0  # no daily costs, no overhead by default


# ── custom params ───────────────────────────────────────────────


def test_custom_maintenance_rate() -> None:
    """Custom maintenance rate per bike per day."""
    params = CostParams(maintenance_per_bike_per_day=1.0)
    engine = CostEngine(params)
    entries = engine.per_tick(tick=1440, tick_in_day=0, total_bikes=50, total_stations=0)
    maint = [e for e in entries if e.category == CostCategory.BIKE_MAINTENANCE]
    assert len(maint) == 1
    assert maint[0].amount == -50.0


def test_custom_lease_rate() -> None:
    """Custom lease rate per station per day."""
    params = CostParams(lease_per_station_per_day=20.0)
    engine = CostEngine(params)
    entries = engine.per_tick(tick=1440, tick_in_day=0, total_bikes=0, total_stations=5)
    lease = [e for e in entries if e.category == CostCategory.STATION_LEASE]
    assert len(lease) == 1
    assert lease[0].amount == -100.0


def test_overhead_per_tick() -> None:
    """Overhead cost is posted every tick."""
    params = CostParams(overhead_per_tick=0.1)
    engine = CostEngine(params)
    entries = engine.per_tick(tick=1, tick_in_day=1, total_bikes=0, total_stations=0)
    overhead = [e for e in entries if e.category == CostCategory.OVERHEAD]
    assert len(overhead) == 1
    assert overhead[0].amount == -0.1


# ── entry metadata ──────────────────────────────────────────────


def test_entry_is_cost() -> None:
    engine = CostEngine()
    entries = engine.per_tick(tick=1440, tick_in_day=0, total_bikes=10, total_stations=5)
    for e in entries:
        assert e.is_cost
        assert e.amount < 0
        assert e.tick == 1440
