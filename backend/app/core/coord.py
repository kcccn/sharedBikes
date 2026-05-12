"""Abstract coordinate type — replaces LatLng across the entire codebase.

Coord(x, y) is a simple 2D Cartesian coordinate. All distance calculations
use Euclidean (L2) distance. There is NO geographic/geodetic meaning.
"""

from __future__ import annotations

import math
from typing import NamedTuple


class Coord(NamedTuple):
    """A 2D Cartesian coordinate on the abstract game board.

    Parameters
    ----------
    x : float
        X-coordinate (horizontal axis).
    y : float
        Y-coordinate (vertical axis).
    """

    x: float
    y: float

    def distance_to(self, other: Coord) -> float:
        """Euclidean distance to *other* Coord."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def bearing_to(self, other: Coord) -> float:
        """Angle (in degrees) from this Coord toward *other*, 0° = east, 90° = north."""
        dx = other.x - self.x
        dy = other.y - self.y
        return (math.degrees(math.atan2(dy, dx)) + 360) % 360

    def midpoint(self, other: Coord) -> Coord:
        """Midpoint between this Coord and *other*."""
        return Coord(
            x=(self.x + other.x) / 2,
            y=(self.y + other.y) / 2,
        )
