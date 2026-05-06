"""Tests for geo utility functions."""

import math

from app.utils.geo import haversine, bearing, midpoint


def test_haversine_same_point() -> None:
    d = haversine(39.9, 116.4, 39.9, 116.4)
    assert d == 0.0


def test_haversine_beijing_to_shanghai() -> None:
    # Approx 1060 km
    d = haversine(39.9042, 116.4074, 31.2304, 121.4737)
    assert 1_000_000 < d < 1_100_000


def test_bearing_north() -> None:
    b = bearing(0.0, 0.0, 10.0, 0.0)
    assert b == 0.0 or abs(b - 360.0) < 1e-9


def test_midpoint() -> None:
    lat, lng = midpoint(40.0, 116.0, 40.0, 117.0)
    assert abs(lat - 40.0) < 0.01
    assert abs(lng - 116.5) < 0.01
