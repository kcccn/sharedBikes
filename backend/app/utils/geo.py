"""Geographic utility functions."""

from __future__ import annotations

import math

# Earth radius in metres (WGS-84)
_EARTH_RADIUS_M = 6_371_000.0


def haversine(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Great-circle distance in metres between two (lat, lng) points."""
    lat1, lng1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lng2 = math.radians(p2[0]), math.radians(p2[1])

    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    # Clamp to avoid floating-point rounding beyond [0, 1]
    a = max(0.0, min(1.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return _EARTH_RADIUS_M * c


def bearing(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Initial bearing in degrees from *p1* toward *p2*."""
    lat1, lng1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lng2 = math.radians(p2[0]), math.radians(p2[1])

    d_lng = lng2 - lng1
    y = math.sin(d_lng) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lng)

    return (math.degrees(math.atan2(y, x)) + 360) % 360


def midpoint(p1: tuple[float, float], p2: tuple[float, float]) -> tuple[float, float]:
    """Midpoint (lat, lng) between two points."""
    lat1, lng1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lng2 = math.radians(p2[0]), math.radians(p2[1])

    bx = math.cos(lat2) * math.cos(lng2 - lng1)
    by = math.cos(lat2) * math.sin(lng2 - lng1)

    lat3 = math.atan2(
        math.sin(lat1) + math.sin(lat2),
        math.sqrt((math.cos(lat1) + bx) ** 2 + by ** 2),
    )
    lng3 = lng1 + math.atan2(by, math.cos(lat1) + bx)

    return (math.degrees(lat3), math.degrees(lng3))
