"""City model — immutable road network, stations, zones, and spatial queries."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NamedTuple


class LatLng(NamedTuple):
    """An immutable geographic coordinate pair."""

    lat: float
    lng: float


@dataclass(frozen=True)
class Node:
    """A road-network node (intersection or dead-end)."""

    node_id: str
    position: LatLng


@dataclass(frozen=True)
class Edge:
    """A directed road segment between two nodes."""

    edge_id: str
    source: str  # source node_id
    target: str  # target node_id
    length_m: float
    max_speed_kmh: float = 30.0


@dataclass(frozen=True)
class Station:
    """A bike docking station."""

    station_id: str
    name: str
    position: LatLng
    capacity: int
    zone_id: str = ""


@dataclass(frozen=True)
class Zone:
    """A named operational zone (e.g. 'CBD', 'University', 'Residential')."""

    zone_id: str
    name: str
    polygon_vertices: tuple[LatLng, ...] = ()


@dataclass(frozen=True)
class City:
    """Immutable city model — built once, queried many times."""

    name: str
    nodes: dict[str, Node]
    edges: dict[str, Edge]
    stations: dict[str, Station]
    zones: dict[str, Zone]

    # ── derived indices ──────────────────────────────────────────────
    _station_positions: dict[str, tuple[float, float]] | None = None

    def __post_init__(self) -> None:
        positions = {
            sid: (s.position.lat, s.position.lng)
            for sid, s in self.stations.items()
        }
        object.__setattr__(self, "_station_positions", positions)

    # ── queries ──────────────────────────────────────────────────────

    def find_nearest_station(self, position: LatLng) -> tuple[str, float] | None:
        """Return (station_id, distance_m) of the nearest station."""
        best: tuple[str, float] | None = None
        best_dist = math.inf
        for sid, (slat, slng) in self._station_positions.items():
            d = _haversine(position.lat, position.lng, slat, slng)
            if d < best_dist:
                best_dist = d
                best = (sid, d)
        return best

    def stations_in_zone(self, zone_id: str) -> list[Station]:
        return [s for s in self.stations.values() if s.zone_id == zone_id]

    def total_capacity(self) -> int:
        return sum(s.capacity for s in self.stations.values())


# ── internal helpers ────────────────────────────────────────────────

def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in metres between two lat/lng points."""
    R = 6_371_000.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    # clamp to [0, 1] to guard against floating-point overshoot
    a = max(0.0, min(1.0, a))
    return R * 2.0 * math.asin(math.sqrt(a))
