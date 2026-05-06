"""City domain: road network, stations, and zones."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NamedTuple


class LatLng(NamedTuple):
    lat: float
    lng: float


@dataclass(frozen=True)
class Node:
    """A road-network node (intersection / OSM node)."""

    node_id: str
    position: LatLng
    elevation_m: float = 0.0


@dataclass(frozen=True)
class Edge:
    """A directed road segment connecting two nodes."""

    edge_id: str
    from_node: str
    to_node: str
    length_m: float
    max_speed_kmh: float = 30.0

    @property
    def travel_time_min(self) -> float:
        return (self.length_m / 1000) / self.max_speed_kmh * 60


@dataclass(frozen=True)
class Station:
    """A bike parking station."""

    station_id: str
    position: LatLng
    capacity: int
    name: str = ""


@dataclass(frozen=True)
class Zone:
    """An operational zone (district / area)."""

    zone_id: str
    name: str
    polygon: list[LatLng]


class City:
    """Immutable city model built once from map data."""

    def __init__(
        self,
        nodes: dict[str, Node],
        edges: dict[str, Edge],
        stations: dict[str, Station],
        zones: dict[str, Zone],
    ) -> None:
        self._nodes = nodes
        self._edges = edges
        self._stations = stations
        self._zones = zones

    @property
    def nodes(self) -> dict[str, Node]:
        return self._nodes

    @property
    def edges(self) -> dict[str, Edge]:
        return self._edges

    @property
    def stations(self) -> dict[str, Station]:
        return self._stations

    @property
    def zones(self) -> dict[str, Zone]:
        return self._zones

    def find_nearest_station(self, position: LatLng) -> tuple[Station | None, float]:
        """Return (nearest station, distance in km) or (None, inf) if no stations."""
        if not self._stations:
            return None, math.inf
        best_station: Station | None = None
        best_dist = math.inf
        for station in self._stations.values():
            d = _haversine_km(position, station.position)
            if d < best_dist:
                best_dist = d
                best_station = station
        return best_station, best_dist


# ---- internal helpers ----


def _haversine_km(a: LatLng, b: LatLng) -> float:
    """Great-circle distance between two LatLng points in km."""
    R = 6371.0
    dlat = math.radians(b.lat - a.lat)
    dlng = math.radians(b.lng - a.lng)
    sin_dlat = math.sin(dlat / 2)
    sin_dlng = math.sin(dlng / 2)
    h = sin_dlat * sin_dlat + math.cos(math.radians(a.lat)) * math.cos(math.radians(b.lat)) * sin_dlng * sin_dlng
    return 2 * R * math.atan2(math.sqrt(h), math.sqrt(1 - h))
