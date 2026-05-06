"""Tests for the city domain model."""

import math

from app.core.city import City, LatLng, Node, Station, _haversine


def test_haversine_same_point() -> None:
    """Distance from a point to itself should be zero."""
    lat, lng = 39.9042, 116.4074
    assert _haversine(lat, lng, lat, lng) == 0.0


def test_haversine_known_distance() -> None:
    """Beijing (39.9042, 116.4074) to Shanghai (31.2304, 121.4737) ≈ 1060 km."""
    d = _haversine(39.9042, 116.4074, 31.2304, 121.4737)
    assert 1000 < d < 1150  # approximate


def test_haversine_numerical_stability() -> None:
    """Close points should not produce NaN."""
    d = _haversine(39.9042, 116.4074, 39.9043, 116.4075)
    assert not math.isnan(d)
    assert d > 0


def test_station_validation() -> None:
    """Station with zero capacity should raise."""
    try:
        Station("bad", "Bad Station", LatLng(0, 0), 0)
        assert False, "Should have raised"
    except ValueError:
        pass


def test_find_nearest_station() -> None:
    """Nearest station query should return the closest."""
    s1 = Station("s1", "S1", LatLng(40.0, 116.4), 10)
    s2 = Station("s2", "S2", LatLng(39.9, 116.4), 10)
    city = City(
        nodes={},
        edges={},
        stations={"s1": s1, "s2": s2},
    )
    nearest = city.find_nearest_station(LatLng(39.95, 116.4))
    assert nearest is not None
    # s1 is at 40.0 (closer to 39.95 than s2 at 39.9)
    assert nearest.station_id == "s1"


def test_find_nearest_station_empty() -> None:
    """Empty city should return None."""
    city = City(nodes={}, edges={}, stations={})
    assert city.find_nearest_station(LatLng(0, 0)) is None


def test_stations_in_zone() -> None:
    """Filter stations by zone name."""
    s1 = Station("s1", "CBD Station A", LatLng(40.0, 116.4), 10)
    s2 = Station("s2", "Residential B", LatLng(39.9, 116.4), 10)
    city = City(nodes={}, edges={}, stations={"s1": s1, "s2": s2})
    cbd_stations = city.stations_in_zone("CBD")
    assert len(cbd_stations) == 1
    assert cbd_stations[0].station_id == "s1"
