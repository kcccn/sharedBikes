"""Geospatial utility functions."""

from __future__ import annotations

import math

_EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great‑circle distance in km between two lat/lng points.

    Uses the atan2 formulation for numerical stability.
    """
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return _EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Initial bearing in degrees from point 1 to point 2."""
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    y = math.sin(dlng) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(
        math.radians(lat1)
    ) * math.cos(math.radians(lat2)) * math.cos(dlng)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def midpoint(lat1: float, lng1: float, lat2: float, lng2: float) -> tuple[float, float]:
    """Midpoint between two coordinates (lat, lng)."""
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    bx = math.cos(lat2_r) * math.cos(dlng)
    by = math.cos(lat2_r) * math.sin(dlng)
    lat3 = math.atan2(
        math.sin(lat1_r) + math.sin(lat2_r),
        math.sqrt((math.cos(lat1_r) + bx) ** 2 + by ** 2),
    )
    lng3 = math.radians(lng1) + math.atan2(by, math.cos(lat1_r) + bx)
    return math.degrees(lat3), math.degrees(lng3)
