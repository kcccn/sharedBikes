"""Tests for fleet domain models."""

from app.core.fleet import Bike, BikeStatus, Fleet, LatLng


def test_add_bike() -> None:
    fleet = Fleet()
    bike = Bike(bike_id="b1")
    fleet.add_bike(bike)
    assert fleet.get_bike("b1") is bike


def test_remove_bike() -> None:
    fleet = Fleet()
    fleet.add_bike(Bike(bike_id="b1"))
    removed = fleet.remove_bike("b1")
    assert removed is not None
    assert fleet.get_bike("b1") is None


def test_remove_nonexistent_returns_none() -> None:
    fleet = Fleet()
    assert fleet.remove_bike("ghost") is None


def test_bikes_at_station() -> None:
    fleet = Fleet()
    b1 = Bike(bike_id="b1", station_id="s1")
    b2 = Bike(bike_id="b2", station_id="s1")
    b3 = Bike(bike_id="b3", station_id="s2")
    fleet.add_bike(b1)
    fleet.add_bike(b2)
    fleet.add_bike(b3)
    assert len(fleet.bikes_at_station("s1")) == 2
    assert len(fleet.bikes_at_station("s2")) == 1


def test_bike_dock_undock() -> None:
    bike = Bike(bike_id="b1")
    assert bike.status == BikeStatus.AVAILABLE
    bike.dock("s1")
    assert bike.station_id == "s1"
    assert bike.status == BikeStatus.AVAILABLE
    bike.undock()
    assert bike.station_id is None
    assert bike.status == BikeStatus.IN_USE


def test_fleet_snapshot() -> None:
    fleet = Fleet()
    fleet.add_bike(Bike(bike_id="b1", status=BikeStatus.AVAILABLE))
    fleet.add_bike(Bike(bike_id="b2", status=BikeStatus.IN_USE))
    snap = fleet.snapshot()
    assert snap.total_bikes == 2
    assert snap.total["AVAILABLE"] == 1
    assert snap.total["IN_USE"] == 1
