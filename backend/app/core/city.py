"""City geometry and network entities."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NamedTuple


class LatLng(NamedTuple):
    """Geographic coordinate in WGS-84."""

    lat: float
    lng: float


@dataclass(frozen=True)
class Node:
    """A road-network node (intersection / point)."""

    node_id: str
    position: LatLng
    elevation: float = 0.0


@dataclass(frozen=True)
class Edge:
    """A directed road segment connecting two nodes."""

    edge_id: str
    from_node: Node
    to_node: Node
    length_m: float  # metres
    max_speed_kmh: float = 30.0


@dataclass(frozen=True)
class Station:
    """A bike docking station."""

    station_id: str
    name: str
    position: LatLng
    capacity: int
    zone_id: str | None = None


@dataclass(frozen=True)
class Zone:
    """A named urban zone (e.g. 'CBD', 'University')."""

    zone_id: str
    name: str
    polygon: list[LatLng]  # simplified closed polygon


@dataclass(frozen=True)
class City:
    """The immutable city road network graph."""

    name: str
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]
    stations: tuple[Station, ...]
    zones: tuple[Zone, ...]

    def find_station(self, station_id: str) -> Station | None:
        return next(
            (s for s in self.stations if s.station_id == station_id),
            None,
        )

    def nearest_station(self, pos: LatLng) -> Station | None:
        """Return the station closest to `pos` by haversine distance."""
        best: Station | None = None
        best_dist = float("inf")
        for s in self.stations:
            d = _haversine(pos.lat, pos.lng, s.position.lat, s.position.lng)
            if d < best_dist:
                best_dist = d
                best = s
        return best


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in metres between two WGS-84 points."""
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
