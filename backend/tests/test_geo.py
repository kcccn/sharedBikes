"""Tests for coordination utility functions."""

from app.core.coord import Coord
from app.utils.geo import haversine_km, bearing, midpoint


def test_haversine_km_same_point() -> None:
    pos = Coord(0.0, 0.0)
    assert haversine_km(pos, pos) == 0.0


def test_haversine_km_euclidean() -> None:
    a = Coord(0.0, 0.0)
    b = Coord(3.0, 4.0)
    # Euclidean distance sqrt(3^2 + 4^2) = 5.0
    assert haversine_km(a, b) == 5.0


def test_bearing_east() -> None:
    a = Coord(0.0, 0.0)
    b = Coord(10.0, 0.0)
    # 0° = east in bearing_to
    assert bearing(a, b) == 0.0


def test_bearing_north() -> None:
    a = Coord(0.0, 0.0)
    b = Coord(0.0, 10.0)
    # 90° = north in bearing_to
    assert abs(bearing(a, b) - 90.0) < 1


def test_midpoint() -> None:
    a = Coord(0.0, 0.0)
    b = Coord(10.0, 10.0)
    m = midpoint(a, b)
    assert abs(m.x - 5.0) < 0.001
    assert abs(m.y - 5.0) < 0.001
