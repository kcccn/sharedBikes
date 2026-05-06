"""Tests for geographic utility functions."""

import math

from app.utils.geo import haversine, bearing, midpoint


class TestHaversine:
    """Great-circle distance tests."""

    def test_known_distance(self):
        """Beijing → Shanghai ~ 1067 km."""
        beijing = (39.9042, 116.4074)
        shanghai = (31.2304, 121.4737)
        d = haversine(beijing, shanghai)
        # Accept a 2 % tolerance
        assert 1_045_000 < d < 1_090_000, f"Expected ~1067 km, got {d:.0f} m"

    def test_zero_distance(self):
        """Same point → 0."""
        assert haversine((0, 0), (0, 0)) == 0.0

    def test_antipodal(self):
        """Antipodal points should produce ~πR distance."""
        d = haversine((0, 0), (0, 180))
        expected = math.pi * 6_371_000
        assert abs(d - expected) < 1_000  # within 1 km

    def test_nan_regression(self):
        """Ensure no NaN for near-identical points (float edge case)."""
        d = haversine((39.9, 116.4), (39.9000001, 116.4000001))
        assert not math.isnan(d)
        assert d > 0


class TestBearing:
    def test_north(self):
        b = bearing((0, 0), (10, 0))
        assert abs(b - 0) < 0.1 or abs(b - 360) < 0.1

    def test_east(self):
        b = bearing((0, 0), (0, 10))
        assert abs(b - 90) < 0.1


class TestMidpoint:
    def test_midpoint_simple(self):
        mid = midpoint((0, 0), (10, 10))
        assert abs(mid[0] - 5.0) < 0.1
        assert abs(mid[1] - 5.0) < 0.1
