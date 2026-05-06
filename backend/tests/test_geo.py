"""Tests for geo utility functions."""

import math

from app.utils.geo import haversine_km, bearing, midpoint, LatLng


class TestHaversine:
    """Verify haversine against known distances."""

    def test_same_point_zero_distance(self):
        p = LatLng(39.9, 116.4)
        assert haversine_km(p, p) == 0.0

    def test_beijing_to_shanghai(self):
        beijing = LatLng(39.9042, 116.4074)
        shanghai = LatLng(31.2304, 121.4737)
        dist = haversine_km(beijing, shanghai)
        # ~1068 km by great-circle
        assert 1000 < dist < 1150

    def test_symmetric(self):
        a = LatLng(40.0, 116.0)
        b = LatLng(41.0, 117.0)
        assert math.isclose(haversine_km(a, b), haversine_km(b, a), rel=1e-9)


class TestBearing:
    def test_north(self):
        a = LatLng(0.0, 0.0)
        b = LatLng(10.0, 0.0)
        assert math.isclose(bearing(a, b), 0.0, abs=1e-3)

    def test_east(self):
        a = LatLng(0.0, 0.0)
        b = LatLng(0.0, 10.0)
        assert math.isclose(bearing(a, b), 90.0, abs=1e-3)


class TestMidpoint:
    def test_midpoint_between_two_points(self):
        a = LatLng(0.0, 0.0)
        b = LatLng(10.0, 10.0)
        m = midpoint(a, b)
        assert 4.9 < m.lat < 5.1
        assert 4.9 < m.lng < 5.1
