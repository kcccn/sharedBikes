"""Tests for the geo utility module."""

import math

from app.utils.geo import haversine, bearing, midpoint


def test_haversine_known() -> None:
    """Beijing → Shanghai ≈ 1060 km."""
    d = haversine(39.9042, 116.4074, 31.2304, 121.4737)
    assert 1000 < d < 1150


def test_haversine_zero() -> None:
    assert haversine(0, 0, 0, 0) == 0.0


def test_haversine_no_nan() -> None:
    """Close coordinates must not produce NaN."""
    d = haversine(39.9042, 116.4074, 39.9042 + 1e-6, 116.4074 + 1e-6)
    assert not math.isnan(d)
    assert d > 0


def test_bearing_north() -> None:
    """Bearing from (0, 0) to (10, 0) should be 0° (north)."""
    b = bearing(0, 0, 10, 0)
    assert b == 0.0


def test_bearing_east() -> None:
    """Bearing from (0, 0) to (0, 10) should be 90° (east)."""
    b = bearing(0, 0, 0, 10)
    assert b == 90.0


def test_midpoint() -> None:
    """Midpoint of (0, 0) and (10, 0) should be ~(5, 0)."""
    lat, lng = midpoint(0, 0, 10, 0)
    assert abs(lat - 5.0) < 0.1
    assert abs(lng - 0.0) < 0.1
