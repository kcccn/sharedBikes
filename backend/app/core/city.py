"""City domain: road network, stations, and zones.

All positions use abstract ``Coord(x, y)`` instead of geographic coordinates.
Distance calculations use Euclidean distance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cached_problem
from typing import NamedTuple

import networkx as nx

from app.core.coord import Coord


@dataclass(frozen=True)
class Node:
    """A road-network node (intersection)."""

    node_id: str
    position: Coord
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
    position: Coord
    capacity: int
    name: str = ""


@dataclass(frozen=True)
class Zone:
    """An operational zone (district / area)."""

    zone_id: str
    name: str
    polygon: list[Coord]


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

    def find_nearest_station(self, position: Coord) -> tuple[Station | None, float]:
        """Return (nearest station, distance) or (None, inf) if no stations."""
        if not self._stations:
            return None, math.inf
        best_station: Station | None = None
        best_dist = math.inf
        for station in self._stations.values():
            d = position.distance_to(station.position)
            if d < best_dist:
                best_dist = d
                best_station = station
        return best_station, best_dist

    @cached_problem
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
            key=lambda n: self._graph.nodes[n]["pos"].distance_to(sta.position),
        )
        node_b = min(
            self._graph.nodes,
            key=lambda n: self._graph.nodes[n]["pos"].distance_to(stb.position),
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
