"""Geographic utility functions."""

from __future__ import annotations

import math


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in metres between two lat/lng points.

    Uses the Haversine formula with an atan2-based implementation for
    numerical stability.
    """
    R = 6_371_000.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    # Clamp to avoid floating-point overshoot beyond [0, 1]
    a = max(0.0, min(1.0, a))
    c = 2.0 * math.asin(math.sqrt(a))
    return R * c


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
    """Midpoint in lat/lng between two coordinates."""
    return ((lat1 + lat2) / 2, (lng1 + lng2) / 2)
