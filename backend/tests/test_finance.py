"""Tests for the financial ledger (finance.py)."""

from app.core.finance import (
    CostCategory,
    Ledger,
    LedgerEntry,
    RevenueCategory,
)


def _make_entry(tick: int, idx: int, amount: float, category=None) -> LedgerEntry:
    return LedgerEntry(
        tick=tick,
        entry_id=f"e{tick}-{idx}",
        category=category or RevenueCategory.TRIP_INCOME,
        amount=amount,
        trip_id=f"trip-{tick}-{idx}" if amount > 0 else None,
    )


# ── Ledger construction & append (chunked) ──────────────────────


def test_empty_ledger() -> None:
    ledger = Ledger()
    assert len(ledger) == 0
    assert ledger.balance() == 0.0
    assert ledger.entries == ()


def test_append_one_chunk() -> None:
    ledger = Ledger()
    entries = [_make_entry(1, 0, 100.0), _make_entry(1, 1, -50.0)]
    ledger = ledger.append(entries)
    assert len(ledger) == 2
    assert ledger.balance() == 50.0


def test_append_multiple_chunks() -> None:
    ledger = Ledger()
    ledger = ledger.append([_make_entry(1, 0, 100.0)])
    ledger = ledger.append([_make_entry(2, 0, -30.0)])
    ledger = ledger.append([_make_entry(3, 0, 20.0)])
    assert len(ledger) == 3
    assert ledger.balance() == 90.0


def test_append_chunked_immutable() -> None:
    """Original ledger is not mutated by append."""
    original = Ledger()
    original.append([_make_entry(1, 0, 100.0)])
    assert len(original) == 0  # original unchanged


# ── query ───────────────────────────────────────────────────────


def test_query_all() -> None:
    ledger = Ledger()
    for t in range(1, 4):
        ledger = ledger.append([_make_entry(t, 0, float(t * 10))])
    results = ledger.query()
    assert len(results) == 3


def test_query_tick_range() -> None:
    ledger = Ledger()
    for t in range(1, 11):
        ledger = ledger.append([_make_entry(t, 0, float(t))])
    results = ledger.query(tick_from=3, tick_to=7)
    assert len(results) == 5
    assert all(3 <= e.tick <= 7 for e in results)


def test_query_by_category() -> None:
    ledger = Ledger()
    ledger = ledger.append([
        _make_entry(1, 0, 100.0, RevenueCategory.TRIP_INCOME),
        _make_entry(1, 1, -50.0, CostCategory.BIKE_MAINTENANCE),
        _make_entry(1, 2, -10.0, CostCategory.STATION_LEASE),
    ])
    results = ledger.query(category=CostCategory.BIKE_MAINTENANCE)
    assert len(results) == 1
    assert results[0].amount == -50.0


def test_query_no_match() -> None:
    ledger = Ledger().append([_make_entry(1, 0, 100.0)])
    results = ledger.query(tick_from=10)
    assert results == []


# ── revenue / cost / profit ─────────────────────────────────────


def test_revenue_total() -> None:
    ledger = Ledger()
    ledger = ledger.append([
        _make_entry(1, 0, 100.0, RevenueCategory.TRIP_INCOME),
        _make_entry(1, 1, -50.0, CostCategory.BIKE_MAINTENANCE),
        _make_entry(2, 0, 200.0, RevenueCategory.TRIP_INCOME),
    ])
    assert ledger.revenue_total() == 300.0


def test_cost_total() -> None:
    ledger = Ledger()
    ledger = ledger.append([
        _make_entry(1, 0, 100.0, RevenueCategory.TRIP_INCOME),
        _make_entry(1, 1, -50.0, CostCategory.BIKE_MAINTENANCE),
        _make_entry(2, 0, -30.0, CostCategory.STATION_LEASE),
    ])
    assert ledger.cost_total() == 80.0


def test_profit() -> None:
    ledger = Ledger()
    ledger = ledger.append([
        _make_entry(1, 0, 100.0, RevenueCategory.TRIP_INCOME),
        _make_entry(1, 1, -50.0, CostCategory.BIKE_MAINTENANCE),
    ])
    assert ledger.profit() == 50.0


def test_revenue_total_with_range() -> None:
    ledger = Ledger()
    for t in range(1, 6):
        ledger = ledger.append([
            _make_entry(t, 0, float(t * 10), RevenueCategory.TRIP_INCOME),
        ])
    # ticks 2..4 → 20 + 30 + 40 = 90
    assert ledger.revenue_total(tick_from=2, tick_to=4) == 90.0


# ── LedgerEntry properties ──────────────────────────────────────


def test_entry_is_revenue() -> None:
    e = _make_entry(1, 0, 100.0, RevenueCategory.TRIP_INCOME)
    assert e.is_revenue
    assert not e.is_cost


def test_entry_is_cost() -> None:
    e = _make_entry(1, 0, -50.0, CostCategory.BIKE_MAINTENANCE)
    assert e.is_cost
    assert not e.is_revenue
