"""City domain model — immutable road network and station topology."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NamedTuple


class LatLng(NamedTuple):
    """Geographic coordinate pair."""

    lat: float
    lng: float


@dataclass(frozen=True)
class Node:
    """A road intersection / point in the city graph."""

    node_id: str
    position: LatLng


@dataclass(frozen=True)
class Edge:
    """A directed road segment connecting two nodes."""

    edge_id: str
    from_node: str
    to_node: str
    length_m: float  # metres


@dataclass(frozen=True)
class Station:
    """A bike docking station."""

    station_id: str
    name: str
    position: LatLng
    capacity: int

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError(f"Station capacity must be > 0, got {self.capacity}")


@dataclass(frozen=True)
class Zone:
    """A named urban zone (e.g. 'CBD', 'Residential-A')."""

    zone_id: str
    name: str
    polygon: tuple[LatLng, ...]  # vertex list (closed)


class City:
    """Immutable city model — road graph + stations + zones.

    Built once at initialisation; never mutated during simulation.
    """

    def __init__(
        self,
        nodes: dict[str, Node],
        edges: dict[str, Edge],
        stations: dict[str, Station],
        zones: dict[str, Zone] | None = None,
    ) -> None:
        self._nodes = nodes
        self._edges = edges
        self._stations = stations
        self._zones = zones or {}

    # ── read-only accessors ──────────────────────────────

    @property
    def nodes(self) -> dict[str, Node]:
        return dict(self._nodes)

    @property
    def edges(self) -> dict[str, Edge]:
        return dict(self._edges)

    @property
    def stations(self) -> dict[str, Station]:
        return dict(self._stations)

    @property
    def zones(self) -> dict[str, Zone]:
        return dict(self._zones)

    def get_station(self, station_id: str) -> Station | None:
        return self._stations.get(station_id)

    def get_node(self, node_id: str) -> Node | None:
        return self._nodes.get(node_id)

    # ── spatial queries ──────────────────────────────────

    def find_nearest_station(self, pos: LatLng) -> Station | None:
        """Return the station closest to *pos* (haversine distance)."""
        best: Station | None = None
        best_dist = math.inf
        for station in self._stations.values():
            d = _haversine(pos.lat, pos.lng, station.position.lat, station.position.lng)
            if d < best_dist:
                best_dist = d
                best = station
        return best

    def stations_in_zone(self, zone_id: str) -> list[Station]:
        """Return all stations belonging to a given zone (simple name‑match)."""
        return [s for s in self._stations.values() if zone_id in s.name or zone_id == ""]


# ── internal helpers ─────────────────────────────────────

_EARTH_RADIUS_KM = 6371.0


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great‑circle distance in km between two lat/lng points."""
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return _EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
