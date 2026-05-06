"""
OSM data ingestion — turn real map data into a routable graph.

Architecture note: this is an **adapter** (Ports & Adapters pattern).
The core simulation never touches OSM directly; it only knows about
GeoPoint and GeoBounds. The geography module translates raw OSM
topology into the road network model that the dispatch engine queries.

Strategy:
  1. Download OSM data within bounds via osmnx.
  2. Simplify the graph (remove dead‑end service roads, merge short edges).
  3. Attach elevation data from SRTM / Open Elevation API.
  4. Expose a clean RoadNetwork with shortest‑path and isochrone queries.

Currently a skeleton — real implementation depends on osmnx + elevation APIs.
"""

from __future__ import annotations

from typing import Protocol

from ..core.models import GeoBounds, GeoPoint


class RoadNetwork(Protocol):
    """Protocol that any road network implementation must satisfy."""

    def shortest_path(self, origin: GeoPoint, dest: GeoPoint) -> list[GeoPoint]:
        """Returns list of waypoints forming the shortest path."""
        ...

    def distance_km(self, origin: GeoPoint, dest: GeoPoint) -> float:
        """Great-circle or routed distance between two points."""
        ...

    def nearest_node(self, point: GeoPoint) -> int:
        """Map a lat/lng to the nearest graph node ID."""
        ...

    def isochrone(self, origin: GeoPoint, minutes: float) -> list[GeoPoint]:
        """Return polygon vertices reachable within *minutes* of cycling."""
        ...


def parse_osm_bounds(bounds: GeoBounds) -> dict:
    """
    Fetch OSM data for the given bounding box.
    Returns a dict summary (number of nodes, edges, etc.)
    This is a placeholder for the real osmnx.graph_from_bbox() call.
    """
    return {
        "bounds": bounds,
        "status": "placeholder — osmnx integration pending",
        "nodes_estimated": 0,
        "edges_estimated": 0,
    }
