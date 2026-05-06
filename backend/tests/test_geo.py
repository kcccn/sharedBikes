"""Tests for geographic utility functions."""
import math
import pytest
from app.utils.geo import haversine, bearing, midpoint


class TestHaversine:
    def test_same_point(self) -> None:
        assert haversine(0.0, 0.0, 0.0, 0.0) == 0.0

    def test_known_distance(self) -> None:
        # Tokyo → Seoul roughly 1154 km
        dist = haversine(35.6762, 139.6503, 37.5665, 126.9780)
        assert 1_100_000 < dist < 1_200_000

    def test_antipodal_small_angle(self) -> None:
        # Very close points should not produce NaN
        d = haversine(45.0, 0.0, 45.0001, 0.0)
        assert not math.isnan(d)
        assert d > 0

    def test_symmetry(self) -> None:
        d1 = haversine(10.0, 20.0, 30.0, 40.0)
        d2 = haversine(30.0, 40.0, 10.0, 20.0)
        assert d1 == pytest.approx(d2, rel=1e-9)


class TestBearing:
    def test_north(self) -> None:
        b = bearing(0.0, 0.0, 10.0, 0.0)
        assert b == pytest.approx(0.0, abs=1)

    def test_east(self) -> None:
        b = bearing(0.0, 0.0, 0.0, 10.0)
        assert b == pytest.approx(90.0, abs=1)


class TestMidpoint:
    def test_midpoint(self) -> None:
        mlat, mlng = midpoint(0.0, 0.0, 10.0, 10.0)
        assert mlat == pytest.approx(5.0)
        assert mlng == pytest.approx(5.0)
