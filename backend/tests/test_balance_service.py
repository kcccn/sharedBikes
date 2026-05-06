"""Tests for balance service."""

from app.core.fleet import Bike, Fleet
from app.core.scheduler import GreedyThresholdStrategy
from app.services.balance_service import BalanceService


def test_balance_service_analyse_empty() -> None:
    strategy = GreedyThresholdStrategy()
    service = BalanceService(strategy=strategy)
    fleet = Fleet()
    report = service.analyse(fleet, station_capacity={})
    assert report.starving_stations == []
    assert report.overflowing_stations == []


def test_balance_service_with_bikes() -> None:
    strategy = GreedyThresholdStrategy()
    service = BalanceService(strategy=strategy)
    fleet = Fleet()
    fleet.add_bike(Bike(bike_id="b1", station_id="s1"))
    fleet.add_bike(Bike(bike_id="b2", station_id="s1"))
    fleet.add_bike(Bike(bike_id="b3", station_id="s2"))

    capacity = {"s1": 10, "s2": 10}
    report = service.analyse(fleet, capacity, threshold_low=0.3, threshold_high=0.7)
    # s1: 2/10 = 20% → starving (below 30%)
    # s2: 1/10 = 10% → starving (below 30%)
    assert "s1" in report.starving_stations
    assert "s2" in report.starving_stations
