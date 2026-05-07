"""City domain: road network, stations, and zones."""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cached_property
from typing import NamedTuple

import networkx as nx


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

    @cached_property
    def _graph(self) -> nx.Graph:
        """Build an undirected NetworkX graph from nodes and edges (cached)."""
        G = nx.Graph()
        for node_id, node in self._nodes.items():
            G.add_node(node_id, pos=node.position)
        for edge_id, edge in self._edges.items():
            G.add_edge(
                edge.from_node,
                edge.to_node,
                id=edge_id,
                length_m=edge.length_m,
                weight=edge.length_m,
            )
        return G

    def shortest_path_distance(self, station_a_id: str, station_b_id: str) -> float | None:
        """Return shortest-path distance in km between two stations along the road network.

        Uses the cached NetworkX graph. Returns ``None`` if either station
        has no nearest road node or the graph is disconnected.
        """
        sta = self._stations.get(station_a_id)
        stb = self._stations.get(station_b_id)
        if sta is None or stb is None:
            return None

        # Find nearest graph node for each station
        node_a = min(
            self._graph.nodes,
            key=lambda n: _haversine_km(self._graph.nodes[n]["pos"], sta.position),
        )
        node_b = min(
            self._graph.nodes,
            key=lambda n: _haversine_km(self._graph.nodes[n]["pos"], stb.position),
        )

        if node_a == node_b:
            return 0.0

        try:
            path_len = nx.shortest_path_length(
                self._graph, source=node_a, target=node_b, weight="weight"
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

        # Convert metres to km
        return path_len / 1000.0


# ---- internal helpers ----


def _haversine_km(a: LatLng, b: LatLng) -> float:
    """Great-circle distance between two LatLng points in km."""
    R = 6371.0
    dlat = math.radians(b.lat - a.lat)
    dlng = math.radians(b.lng - a.lng)
    sin_dlat = math.sin(dlat / 2)
    sin_dlng = math.sin(dlng / 2)
    h = sin_dlat * sin_dlat + math.cos(math.radians(a.lat)) * math.cos(
        math.radians(b.lat)
    ) * sin_dlng * sin_dlng
    return 2 * R * math.atan2(math.sqrt(h), math.sqrt(1 - h))
