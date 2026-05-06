"""Tests for geo utility functions."""

import math

from app.utils.geo import haversine_km, bearing, midpoint, LatLng


def test_haversine_km_same_point() -> None:
    p = LatLng(lat=39.9, lng=116.4)
    assert haversine_km(p, p) == 0.0


def test_haversine_km_beijing_shanghai() -> None:
    beijing = LatLng(lat=39.9042, lng=116.4074)
    shanghai = LatLng(lat=31.2304, lng=121.4737)
    dist = haversine_km(beijing, shanghai)
    # ~1068 km as the crow flies
    assert 1000 < dist < 1200


def test_haversine_km_antipodal() -> None:
    # Points at same latitude on opposite meridians
    a = LatLng(lat=0.0, lng=0.0)
    b = LatLng(lat=0.0, lng=180.0)
    dist = haversine_km(a, b)
    # half the earth's circumference ≈ 20015 km
    assert 19900 < dist < 20100


def test_bearing_north() -> None:
    a = LatLng(lat=0.0, lng=0.0)
    b = LatLng(lat=10.0, lng=0.0)
    assert bearing(a, b) == 0.0


def test_bearing_east() -> None:
    a = LatLng(lat=0.0, lng=0.0)
    b = LatLng(lat=0.0, lng=10.0)
    assert math.isclose(bearing(a, b), 90.0, rel_tol=1e-9)


def test_midpoint() -> None:
    a = LatLng(lat=0.0, lng=0.0)
    b = LatLng(lat=10.0, lng=10.0)
    m = midpoint(a, b)
    assert math.isclose(m.lat, 5.0, rel_tol=1e-6)
    assert math.isclose(m.lng, 5.0, rel_tol=1e-6)
