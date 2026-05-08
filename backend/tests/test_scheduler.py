"""Tests for scheduler / rebalancing strategy."""

import pytest

from app.core.fleet import Bike, BikeStatus, Fleet
from app.core.scheduler import DispatchOrder, GreedyThresholdStrategy


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


# ── Phase 3: apply_orders tests ─────────────────────────────────


def test_apply_orders_moves_bikes() -> None:
    """apply_orders should physically move bikes between stations."""
    fleet = Fleet()
    # Add 5 bikes to station "a"
    for i in range(5):
        fleet.add_bike(Bike(bike_id=f"b{i}", station_id="a", status=BikeStatus.AVAILABLE))
    # Add 3 bikes to station "b"
    for i in range(5, 8):
        fleet.add_bike(Bike(bike_id=f"b{i}", station_id="b", status=BikeStatus.AVAILABLE))

    strategy = GreedyThresholdStrategy()
    orders = [
        DispatchOrder(order_id="o1", from_station="a", to_station="c", count=3),
    ]
    executed = strategy.apply_orders(orders, fleet)

    assert len(executed) == 1
    assert executed[0] == ("a", "c", 3)

    # Verify bikes actually moved
    assert len(fleet.bikes_at_station("a")) == 2  # 5 - 3
    assert len(fleet.bikes_at_station("c")) == 3  # 0 + 3


def test_apply_orders_respects_available_bikes() -> None:
    """Should not move more bikes than available at source."""
    fleet = Fleet()
    fleet.add_bike(Bike(bike_id="b1", station_id="a", status=BikeStatus.AVAILABLE))

    strategy = GreedyThresholdStrategy()
    orders = [
        DispatchOrder(order_id="o1", from_station="a", to_station="b", count=5),
    ]
    executed = strategy.apply_orders(orders, fleet)

    # Only 1 bike available, so only 1 moved
    assert executed[0] == ("a", "b", 1)


def test_apply_orders_skips_in_use_bikes() -> None:
    """Should not move bikes that are currently in use."""
    fleet = Fleet()
    fleet.add_bike(Bike(bike_id="b1", station_id="a", status=BikeStatus.AVAILABLE))
    fleet.add_bike(Bike(bike_id="b2", station_id="a", status=BikeStatus.IN_USE))

    strategy = GreedyThresholdStrategy()
    orders = [
        DispatchOrder(order_id="o1", from_station="a", to_station="b", count=2),
    ]
    executed = strategy.apply_orders(orders, fleet)

    # Only the AVAILABLE bike can be moved
    assert executed[0] == ("a", "b", 1)


def test_apply_orders_empty_orders() -> None:
    """Empty orders should produce empty results."""
    fleet = Fleet()
    strategy = GreedyThresholdStrategy()
    executed = strategy.apply_orders([], fleet)
    assert executed == []


def test_apply_orders_multi_batch() -> None:
    """Multiple orders should each produce a movement record."""
    fleet = Fleet()
    for i in range(10):
        fleet.add_bike(Bike(bike_id=f"b{i}", station_id="a", status=BikeStatus.AVAILABLE))
    for i in range(10, 15):
        fleet.add_bike(Bike(bike_id=f"b{i}", station_id="b", status=BikeStatus.AVAILABLE))

    strategy = GreedyThresholdStrategy()
    orders = [
        DispatchOrder(order_id="o1", from_station="a", to_station="c", count=4),
        DispatchOrder(order_id="o2", from_station="b", to_station="c", count=2),
    ]
    executed = strategy.apply_orders(orders, fleet)

    assert len(executed) == 2
    assert executed[0] == ("a", "c", 4)
    assert executed[1] == ("b", "c", 2)
    assert len(fleet.bikes_at_station("c")) == 6
