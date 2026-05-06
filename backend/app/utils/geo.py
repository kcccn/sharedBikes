"""Geospatial utility functions."""

from __future__ import annotations

import math
from typing import NamedTuple


class LatLng(NamedTuple):
    lat: float
    lng: float


def haversine_km(a: LatLng, b: LatLng) -> float:
    """Great-circle distance between two points in km."""
    R = 6371.0
    dlat = math.radians(b.lat - a.lat)
    dlng = math.radians(b.lng - a.lng)
    sin_dlat = math.sin(dlat / 2)
    sin_dlng = math.sin(dlng / 2)
    h = sin_dlat * sin_dlat + math.cos(math.radians(a.lat)) * math.cos(math.radians(b.lat)) * sin_dlng * sin_dlng
    return 2 * R * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def bearing(a: LatLng, b: LatLng) -> float:
    """Initial bearing from a to b in degrees."""
    dlat = math.radians(b.lat - a.lat)
    dlng = math.radians(b.lng - a.lng)
    y = math.sin(dlng) * math.cos(math.radians(b.lat))
    x = math.cos(math.radians(a.lat)) * math.sin(math.radians(b.lat)) - \
        math.sin(math.radians(a.lat)) * math.cos(math.radians(b.lat)) * math.cos(dlng)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def midpoint(a: LatLng, b: LatLng) -> LatLng:
    """Midpoint between two coordinates."""
    dlat = math.radians(b.lat - a.lat)
    dlng = math.radians(b.lng - a.lng)
    lat1, lng1 = math.radians(a.lat), math.radians(a.lng)
    lat2 = math.radians(b.lat)
    bx = math.cos(lat2) * math.cos(dlng)
    by = math.cos(lat2) * math.sin(dlng)
    lat3 = math.atan2(math.sin(lat1) + math.sin(lat2),
                      math.sqrt((math.cos(lat1) + bx) ** 2 + by ** 2))
    lng3 = lng1 + math.atan2(by, math.cos(lat1) + bx)
    return LatLng(lat=math.degrees(lat3), lng=math.degrees(lng3))
