"""Tests for fleet domain models."""

import pytest

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


# ── relocate_bikes: validation ──────────────────────────────────


def test_relocate_bikes_happy_path() -> None:
    """Bikes are moved when both stations are valid."""
    fleet = Fleet()
    fleet.add_bike(Bike(bike_id="b1", station_id="s1", status=BikeStatus.AVAILABLE))
    fleet.add_bike(Bike(bike_id="b2", station_id="s1", status=BikeStatus.AVAILABLE))

    moved = fleet.relocate_bikes("s1", "s2", 1, valid_stations={"s1", "s2"})
    assert moved == 1
    assert fleet.get_bike("b1").station_id == "s2"  # type: ignore[union-attr]
    assert fleet.get_bike("b2").station_id == "s1"  # type: ignore[union-attr]


def test_relocate_bikes_raises_on_invalid_to_station() -> None:
    """ValueError is raised when to_station is not in valid_stations."""
    fleet = Fleet()
    fleet.add_bike(Bike(bike_id="b1", station_id="s1", status=BikeStatus.AVAILABLE))

    with pytest.raises(ValueError, match="Unknown to_station.*phantom"):
        fleet.relocate_bikes("s1", "phantom", 1, valid_stations={"s1", "s2"})


def test_relocate_bikes_raises_on_invalid_from_station() -> None:
    """ValueError is raised when from_station is not in valid_stations."""
    fleet = Fleet()
    fleet.add_bike(Bike(bike_id="b1", station_id="s1", status=BikeStatus.AVAILABLE))

    with pytest.raises(ValueError, match="Unknown from_station.*phantom"):
        fleet.relocate_bikes("phantom", "s1", 1, valid_stations={"s1", "s2"})


def test_relocate_bikes_raises_on_both_invalid() -> None:
    """from_station is validated first when both stations are invalid."""
    fleet = Fleet()
    with pytest.raises(ValueError, match="Unknown from_station.*ghost"):
        fleet.relocate_bikes("ghost", "phantom", 1, valid_stations={"s1"})


def test_relocate_bikes_no_validation_when_none_passed() -> None:
    """Backward compat: no validation when valid_stations is None."""
    fleet = Fleet()
    fleet.add_bike(Bike(bike_id="b1", station_id="s1", status=BikeStatus.AVAILABLE))

    moved = fleet.relocate_bikes("s1", "nonsense", 1, valid_stations=None)
    assert moved == 1  # silently moves to phantom (backward compat)
    assert fleet.get_bike("b1").station_id == "nonsense"  # type: ignore[union-attr]


def test_relocate_bikes_skips_in_use_bikes() -> None:
    """Only AVAILABLE bikes are relocated."""
    fleet = Fleet()
    fleet.add_bike(Bike(bike_id="b1", station_id="s1", status=BikeStatus.AVAILABLE))
    fleet.add_bike(Bike(bike_id="b2", station_id="s1", status=BikeStatus.IN_USE))

    moved = fleet.relocate_bikes("s1", "s2", 5, valid_stations={"s1", "s2"})
    assert moved == 1
    assert fleet.get_bike("b1").station_id == "s2"  # type: ignore[union-attr]
    assert fleet.get_bike("b2").station_id == "s1"  # type: ignore[union-attr]
