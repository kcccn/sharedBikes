"""Tests for geospatial utility functions."""

from __future__ import annotations

import math

import pytest

from app.utils.geo import bearing, haversine, midpoint


class TestHaversine:
    def test_same_point_zero_distance(self):
        assert haversine(0.0, 0.0, 0.0, 0.0) == 0.0

    def test_equator_degree(self):
        # 1 degree of latitude at equator ≈ 111.195 km
        dist = haversine(0.0, 0.0, 1.0, 0.0)
        assert 111_000 < dist < 112_000

    def test_known_distance(self):
        # London (51.5, -0.12) → Paris (48.86, 2.35) ≈ 344 km
        dist = haversine(51.5, -0.12, 48.86, 2.35)
        assert 340_000 < dist < 350_000

    def test_antipodal(self):
        # North Pole → South Pole ≈ half the earth's circumference
        dist = haversine(90.0, 0.0, -90.0, 0.0)
        expected = math.pi * 6_371_000.0  # half circumference
        assert abs(dist - expected) < 100  # within 100m

    def test_no_nan_for_near_antipodal(self):
        """Regression: the old math.asin(math.sqrt(h)) formulation can
        produce NaN when h marginally exceeds 1.0 due to FP error."""
        for lat in [0.0, 30.0, 60.0, 89.999]:
            d = haversine(lat, 0.0, -lat, 180.0)
            assert not math.isnan(d), f"NaN at lat={lat}"


class TestBearing:
    def test_north(self):
        b = bearing(0.0, 0.0, 10.0, 0.0)
        assert abs(b - 0) < 0.5 or abs(b - 360) < 0.5

    def test_east(self):
        b = bearing(0.0, 0.0, 0.0, 10.0)
        assert abs(b - 90) < 0.5

    def test_south(self):
        b = bearing(10.0, 0.0, 0.0, 0.0)
        assert abs(b - 180) < 0.5

    def test_west(self):
        b = bearing(0.0, 10.0, 0.0, 0.0)
        assert abs(b - 270) < 0.5


class TestMidpoint:
    def test_midpoint_same_point(self):
        m = midpoint(10.0, 20.0, 10.0, 20.0)
        assert m == (10.0, 20.0)

    def test_midpoint_equator(self):
        m = midpoint(-10.0, 0.0, 10.0, 0.0)
        assert abs(m[0]) < 0.01  # very close to equator
