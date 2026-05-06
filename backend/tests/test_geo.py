"""Tests for geospatial utility functions."""

from app.utils.geo import haversine_km, bearing, midpoint, LatLng


def test_haversine_km_same_point() -> None:
    pos = LatLng(39.9, 116.4)
    assert haversine_km(pos, pos) == 0.0


def test_haversine_km_beijing_shanghai() -> None:
    beijing = LatLng(39.9042, 116.4074)
    shanghai = LatLng(31.2304, 121.4737)
    d = haversine_km(beijing, shanghai)
    # ~1060 km
    assert 1000 < d < 1100


def test_bearing_north() -> None:
    a = LatLng(0, 0)
    b = LatLng(10, 0)
    assert bearing(a, b) == 0.0  # due north


def test_bearing_east() -> None:
    a = LatLng(0, 0)
    b = LatLng(0, 10)
    assert abs(bearing(a, b) - 90.0) < 1


def test_midpoint() -> None:
    a = LatLng(0, 0)
    b = LatLng(10, 10)
    m = midpoint(a, b)
    assert abs(m.lat - 5.0) < 0.5
    assert abs(m.lng - 5.0) < 0.5
