"""Tests for geo utilities."""

from __future__ import annotations

import math

from app.core.city import LatLng
from app.utils.geo import haversine, bearing, midpoint


def test_haversine_same_point() -> None:
    p = LatLng(39.9, 116.4)
    assert haversine(p, p) == 0.0


def test_haversine_known_distance() -> None:
    # Beijing (39.9, 116.4) → roughly 111 km north ≈ 1 degree latitude
    a = LatLng(39.9, 116.4)
    b = LatLng(40.9, 116.4)
    dist = haversine(a, b)
    assert 110_000 < dist < 112_000  # ~111 km


def test_bearing_cardinal() -> None:
    a = LatLng(0, 0)
    north = LatLng(10, 0)
    east = LatLng(0, 10)
    assert bearing(a, north) == pytest.approx(0, abs=1)
    assert bearing(a, east) == pytest.approx(90, abs=1)


def test_midpoint() -> None:
    a = LatLng(40.0, 116.0)
    b = LatLng(40.0, 117.0)
    m = midpoint(a, b)
    assert m.lat == pytest.approx(40.0, abs=0.01)
    assert m.lng == pytest.approx(116.5, abs=0.01)
