"""Spatial math utilities — distance, bearing, grid indexing."""

from __future__ import annotations

import math

from app.core.city import LatLng

R_EARTH_M = 6_371_000.0


def haversine(a: LatLng, b: LatLng) -> float:
    """Great-circle distance in metres."""
    lat1, lon1 = math.radians(a.lat), math.radians(a.lng)
    lat2, lon2 = math.radians(b.lat), math.radians(b.lng)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * R_EARTH_M * math.asin(math.sqrt(h))


def bearing(a: LatLng, b: LatLng) -> float:
    """Initial bearing (degrees) from a to b."""
    lat1, lon1 = math.radians(a.lat), math.radians(a.lng)
    lat2, lon2 = math.radians(b.lat), math.radians(b.lng)
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(
        dlon
    )
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def midpoint(a: LatLng, b: LatLng) -> LatLng:
    """Midpoint along the great-circle arc."""
    lat1, lon1 = math.radians(a.lat), math.radians(a.lng)
    lat2, lon2 = math.radians(b.lat), math.radians(b.lng)
    bx = math.cos(lat2) * math.cos(lon2 - lon1)
    by = math.cos(lat2) * math.sin(lon2 - lon1)
    lat3 = math.atan2(
        math.sin(lat1) + math.sin(lat2),
        math.sqrt((math.cos(lat1) + bx) ** 2 + by**2),
    )
    lon3 = lon1 + math.atan2(by, math.cos(lat1) + bx)
    return LatLng(math.degrees(lat3), math.degrees(lon3))
