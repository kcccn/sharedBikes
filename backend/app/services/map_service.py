"""Map service — loads and caches City from OSM data.

Phase 1 (current): real OSM parsing via osmnx.
Phase 2+:           add persistent caching (e.g. GeoPackage / Parquet).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.core.city import City, LatLng, Node, Edge, Station, Zone
from app.services.osm_parser import (
    OSMError,
    parse_from_bbox,
    parse_from_file,
    parse_from_place,
)


class MapService:
    """Service responsible for loading city map data from OSM sources."""

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        self._cache_dir = Path(cache_dir) if cache_dir else None

    # ── Public API ───────────────────────────────────────────────────

    def load_city(self, city_name: str) -> City:
        """Load or build a City from OSM data.

        Delegates to the appropriate parser based on the input:

        - If *city_name* resolves to a known OSM place (e.g. ``"Beijing"``),
          uses ``parse_from_place``.
        - Otherwise falls back to the legacy stub (for tests that depend
          on the minimal city).
        """
        # Phase‑1: try place-based lookup
        try:
            return parse_from_place(city_name)
        except OSMError:
            pass

        # Fallback: minimal test city (same as Phase-0 stub)
        return self._build_minimal_city(city_name)

    def load_from_bbox(
        self,
        north: float,
        south: float,
        east: float,
        west: float,
    ) -> City:
        """Load a City from a bounding box."""
        return parse_from_bbox(north=north, south=south, east=east, west=west)

    def load_from_file(self, filepath: str | Path) -> City:
        """Load a City from a local ``.osm.pbf`` or ``.osm`` file."""
        return parse_from_file(filepath)

    # ── Internal helpers ─────────────────────────────────────────────

    @staticmethod
    def _build_minimal_city(name: str) -> City:
        """Return a minimal City with a single node (used as fallback)."""
        center = LatLng(lat=39.9042, lng=116.4074)
        nodes = {"n1": Node(node_id="n1", position=center)}
        edges: dict[str, Edge] = {}
        stations: dict[str, Station] = {}
        zones: dict[str, Zone] = {}
        return City(nodes=nodes, edges=edges, stations=stations, zones=zones)
