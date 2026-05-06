"""Geospatial utilities — distance, bearing, midpoint computations."""

from __future__ import annotations

import math

# WGS-84 ellipsoid semi-major axis (metres)
EARTH_RADIUS_M = 6_371_000.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Great-circle distance in metres between two points on the WGS-84 sphere.

    Uses the atan2-based formulation to avoid NaN from floating-point errors
    when h marginally exceeds 1.0.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_M * c


def haversine_ll(lat_a: float, lng_a: float, lat_b: float, lng_b: float) -> float:
    """Convenience wrapper accepting two (lat, lng) pairs."""
    return haversine(lat_a, lng_a, lat_b, lng_b)


def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Initial bearing (degrees clockwise from true north) from point 1 to point 2.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dlambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(
        dlambda
    )
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def midpoint(lat1: float, lon1: float, lat2: float, lon2: float) -> tuple[float, float]:
    """Midpoint (lat, lon) of the great-circle arc between two points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)

    bx = math.cos(phi2) * math.cos(dlambda)
    by = math.cos(phi2) * math.sin(dlambda)
    lat_mid = math.atan2(
        math.sin(phi1) + math.sin(phi2),
        math.sqrt((math.cos(phi1) + bx) ** 2 + by ** 2),
    )
    lon_mid = math.radians(lon1) + math.atan2(by, math.cos(phi1) + bx)
    return math.degrees(lat_mid), math.degrees(lon_mid)
