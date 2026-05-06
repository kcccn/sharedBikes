"""City model — the immutable road network and station layout."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NamedTuple


class LatLng(NamedTuple):
    """A geographical point (latitude, longitude)."""

    lat: float
    lng: float


@dataclass(frozen=True)
class Node:
    """A node in the road network (intersection / junction)."""

    id: str
    position: LatLng


@dataclass(frozen=True)
class Edge:
    """A directed road segment connecting two nodes."""

    id: str
    from_node: str
    to_node: str
    length_m: float
    speed_limit_kmh: float = 30.0


@dataclass
class Station:
    """A bike station / docking point."""

    id: str
    name: str
    position: LatLng
    capacity: int
    altitude_m: float = 0.0


@dataclass(frozen=True)
class Zone:
    """An operational zone (e.g. 'CBD', 'Residential-1')."""

    id: str
    name: str
    polygon: tuple[LatLng, ...]  # closed polygon vertices


@dataclass
class City:
    """Immutable city definition — built once and read-only throughout a simulation."""

    id: str
    name: str
    nodes: dict[str, Node]
    edges: dict[str, Edge]
    stations: dict[str, Station]
    zones: dict[str, Zone]

    def find_nearest_station(self, position: LatLng) -> Station | None:
        """Return the station closest to *position* (Euclidean approximation)."""
        best: Station | None = None
        best_dist = math.inf
        for station in self.stations.values():
            d = (station.position.lat - position.lat) ** 2 + (
                station.position.lng - position.lng
            ) ** 2
            if d < best_dist:
                best_dist = d
                best = station
        return best
