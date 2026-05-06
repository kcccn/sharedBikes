"""City domain — road network topology, zones, and spatial queries."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple

from app.utils.geo import haversine


class ZoneType(Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    BUSINESS = "business"
    TRANSIT = "transit"  # metro / bus hub
    MIXED = "mixed"


class RoadClass(Enum):
    HIGHWAY = "highway"
    MAIN = "main"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    RESIDENTIAL = "residential"
    PATH = "path"


class LatLng(NamedTuple):
    """A pair of (lat, lng) coordinates on the WGS-84 reference ellipsoid."""

    lat: float
    lng: float


@dataclass
class Node:
    """A vertex in the road network graph."""

    id: str
    position: LatLng
    elevation_m: float = 0.0


@dataclass
class Edge:
    """A directed or undirected road segment between two nodes."""

    id: str
    from_node: str
    to_node: str
    length_m: float
    road_class: RoadClass
    max_speed_kmh: float = 30.0


@dataclass
class Station:
    """A bike parking / docking point (P-point)."""

    id: str
    position: LatLng
    capacity: int
    zone_id: str | None = None
    is_no_parking_zone: bool = False


@dataclass
class Zone:
    """An urban zone with a dominant land-use type."""

    id: str
    name: str
    zone_type: ZoneType
    center: LatLng
    stations: list[str] = field(default_factory=list)


@dataclass
class City:
    """
    Immutable-ish city model built from OSM data.

    Once constructed, the graph is read-only for the duration of a
    simulation run. Mutation happens on the *fleet* and *demand* side.
    """

    name: str
    bounds: tuple[LatLng, LatLng]  # (south-west, north-east)
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: dict[str, Edge] = field(default_factory=dict)
    stations: dict[str, Station] = field(default_factory=dict)
    zones: dict[str, Zone] = field(default_factory=dict)

    def find_nearest_station(self, pos: LatLng) -> Station | None:
        """Return the nearest station to *pos* (Naive O(n) — optimise with spatial index later)."""
        if not self.stations:
            return None
        best: tuple[float, Station | None] = (float("inf"), None)
        for st in self.stations.values():
            d = haversine(pos.lat, pos.lng, st.position.lat, st.position.lng)
            if d < best[0]:
                best = (d, st)
        return best[1]

    def stations_in_zone(self, zone_id: str) -> list[Station]:
        return [s for s in self.stations.values() if s.zone_id == zone_id]
