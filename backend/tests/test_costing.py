"""Tests for the cost engine."""

from app.core.costing import CostEngine, CostParams
from app.core.finance import CostCategory, RevenueCategory


def test_per_tick_first_tick_of_day() -> None:
    """Tick 0 of a new day should include maintenance + lease costs."""
    engine = CostEngine()
    entries = engine.per_tick(tick=1440, tick_in_day=0, total_bikes=100, total_stations=10)

    # 100 * 0.5 = 50, 10 * 10 = 100
    costs = {e.entry_id: e for e in entries if e.is_cost}
    assert "cost-maint-1440" in costs
    assert "cost-lease-1440" in costs
    assert costs["cost-maint-1440"].amount == -50.0
    assert costs["cost-lease-1440"].amount == -100.0


def test_per_tick_mid_day_has_no_fixed_costs() -> None:
    """Mid-day ticks should have no fixed costs (only overhead if set)."""
    engine = CostEngine(CostParams(overhead_per_tick=0.01))
    entries = engine.per_tick(tick=100, tick_in_day=100, total_bikes=100, total_stations=10)

    assert all(e.entry_id == "cost-overhead-100" for e in entries)


def test_per_tick_zero_cost_params() -> None:
    """Zero-cost params should produce no entries."""
    engine = CostEngine(CostParams(maintenance_per_bike_per_day=0, lease_per_station_per_day=0))
    entries = engine.per_tick(tick=1440, tick_in_day=0, total_bikes=100, total_stations=10)
    assert len(entries) == 0


def test_per_tick_custom_params() -> None:
    """Custom cost params should produce correct amounts."""
    params = CostParams(
        maintenance_per_bike_per_day=1.0,
        lease_per_station_per_day=20.0,
    )
    engine = CostEngine(params)
    entries = engine.per_tick(tick=1440, tick_in_day=0, total_bikes=50, total_stations=5)
    costs = {e.entry_id: e for e in entries}

    assert costs["cost-maint-1440"].amount == -50.0   # 50 * 1.0
    assert costs["cost-lease-1440"].amount == -100.0   # 5 * 20.0


# ── Phase 3: dispatch_entries tests ─────────────────────────────


def test_dispatch_entries_single_movement() -> None:
    """Single dispatch movement should produce one cost and one fee entry."""
    engine = CostEngine()
    movements = [("s1", "s2", 3)]
    entries = engine.dispatch_entries(tick=100, movements=movements)

    assert len(entries) == 2

    cost_entry = entries[0]
    assert cost_entry.entry_id == "cost-dispatch-100-0"
    assert cost_entry.category == CostCategory.DISPATCH_COST
    assert cost_entry.amount == -6.0  # 3 * 2.0
    assert cost_entry.tick == 100

    fee_entry = entries[1]
    assert fee_entry.entry_id == "rev-dispatch-fee-100-0"
    assert fee_entry.category == RevenueCategory.DISPATCH_FEE
    assert fee_entry.amount == 3.0  # 3 * 1.0
    assert fee_entry.tick == 100


def test_dispatch_entries_multiple_movements() -> None:
    """Multiple movements should produce separate entry pairs."""
    engine = CostEngine()
    movements = [
        ("s1", "s2", 2),
        ("s3", "s4", 5),
    ]
    entries = engine.dispatch_entries(tick=200, movements=movements)

    assert len(entries) == 4

    # First movement: 2 bikes
    assert entries[0].amount == -4.0  # 2 * 2.0
    assert entries[1].amount == 2.0   # 2 * 1.0

    # Second movement: 5 bikes
    assert entries[2].amount == -10.0  # 5 * 2.0
    assert entries[3].amount == 5.0    # 5 * 1.0


def test_dispatch_entries_no_movements() -> None:
    """Empty movements list should produce no entries."""
    engine = CostEngine()
    entries = engine.dispatch_entries(tick=300, movements=[])
    assert entries == []


def test_dispatch_entries_custom_params() -> None:
    """Custom dispatch cost/fee params should be reflected."""
    params = CostParams(dispatch_cost_per_bike=5.0, dispatch_fee_per_bike=2.5)
    engine = CostEngine(params)
    movements = [("s1", "s2", 4)]
    entries = engine.dispatch_entries(tick=400, movements=movements)

    assert len(entries) == 2
    assert entries[0].amount == -20.0  # 4 * 5.0
    assert entries[1].amount == 10.0   # 4 * 2.5
