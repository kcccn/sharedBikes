"""Coordination utility functions — thin wrappers around ``Coord`` methods.

This module exists for backward compatibility with code that calls
``haversine_km(a, b)`` etc. New code should call ``a.distance_to(b)``
directly on ``Coord`` instances.
"""

from __future__ import annotations

from app.core.coord import Coord

# Re-export Coord so existing imports like:
#   from app.utils.geo import Coord, haversine_km
# continue to work.
# ruff: noqa: F401
Coord = Coord


def haversine_km(a: Coord, b: Coord) -> float:
    """Euclidean distance between two Coords (same as ``a.distance_to(b)``).

    .. deprecated::
        Use ``a.distance_to(b)`` directly on ``Coord`` instances.
    """
    return a.distance_to(b)


def bearing(a: Coord, b: Coord) -> float:
    """Angle (degrees) from a toward b, 0° = east, 90° = north.

    .. deprecated::
        Use ``a.bearing_to(b)`` directly on ``Coord`` instances.
    """
    return a.bearing_to(b)


def midpoint(a: Coord, b: Coord) -> Coord:
    """Midpoint between two coordinates.

    .. deprecated::
        Use ``a.midpoint(b)`` directly on ``Coord`` instances.
    """
    return a.midpoint(b)
