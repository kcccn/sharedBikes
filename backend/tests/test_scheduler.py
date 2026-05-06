"""Tests for scheduler / rebalancing strategy."""

from app.core.scheduler import GreedyThresholdStrategy


def test_greedy_threshold_empty_city() -> None:
    strategy = GreedyThresholdStrategy()
    report = strategy.analyse({}, {})
    assert report.starving_stations == []
    assert report.overflowing_stations == []
    assert report.suggested_orders == []


def test_greedy_threshold_identifies_starving_and_overflowing() -> None:
    strategy = GreedyThresholdStrategy()
    inventory = {
        "s1": 0,   # starving (0/20 = 0%)
        "s2": 18,  # overflowing (18/20 = 90%)
        "s3": 10,  # healthy (10/20 = 50%)
    }
    capacity = {"s1": 20, "s2": 20, "s3": 20}
    report = strategy.analyse(inventory, capacity)

    assert "s1" in report.starving_stations
    assert "s2" in report.overflowing_stations
    assert "s3" in report.healthy_stations
    assert len(report.suggested_orders) > 0


def test_greedy_threshold_zero_capacity_skipped() -> None:
    """Stations with capacity <= 0 should be treated as healthy (not starving/overflowing)."""
    strategy = GreedyThresholdStrategy()
    inventory = {"s1": 0}
    capacity = {"s1": 0}
    report = strategy.analyse(inventory, capacity)
    assert "s1" in report.healthy_stations
    assert "s1" not in report.starving_stations
