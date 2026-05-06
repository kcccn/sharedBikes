"""Map service — loads and caches City from OSM data via osmnx."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any

import networkx as nx

from app.core.city import City, Edge, LatLng, Node, Station, Zone

logger = logging.getLogger(__name__)


class CityImportErrorCode(Enum):
    CITY_NOT_FOUND = "CITY_NOT_FOUND"
    NETWORK_ERROR = "NETWORK_ERROR"
    DATA_TOO_LARGE = "DATA_TOO_LARGE"
    INSUFFICIENT_ROADS = "INSUFFICIENT_ROADS"
    PARSING_ERROR = "PARSING_ERROR"


class CityImportError(Exception):
    """Raised when city import from OSM fails."""

    def __init__(self, code: CityImportErrorCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"[{code.value}] {message}")


class MapService:
    """Service responsible for loading city map data from OpenStreetMap.

    Phase 1 uses **osmnx** for city boundary-based import with configurable
    road-type filtering and automatic station generation via betweenness
    centrality and clustering.
    """

    # Default road types to include — excludes residential/footpath for
    # simulation-level granularity.  Pass ``road_types`` to ``load_city()``
    # to override.
    DEFAULT_ROAD_TYPES = {"primary", "secondary", "tertiary"}

    # osmnx custom_filter fragment for the default road types above.
    _DEFAULT_FILTER = (
        '["highway"~"primary|secondary|tertiary"]'
    )

    def load_city(
        self,
        city_name: str,
        *,
        road_types: set[str] | None = None,
        n_stations: int = 200,
        station_cluster_eps_m: float = 200.0,
    ) -> City:
        """Load a real city from OpenStreetMap via osmnx.

        Parameters
        ----------
        city_name:
            City name passed to ``osmnx.graph_from_place()``,
            e.g. ``"Beijing, China"`` or ``"Shanghai, China"``.
        road_types:
            Set of OSM highway tags to keep.  Defaults to
            ``{"primary", "secondary", "tertiary"}``.
        n_stations:
            Number of stations to generate (top-N by betweenness centrality).
        station_cluster_eps_m:
            Maximum distance in metres for merging nearby station candidates.

        Returns
        -------
        A fully populated ``City`` with nodes, edges, stations, and zones.

        Raises
        ------
        CityImportError
            If the city cannot be found, the network is unreachable, the data
            is too large, or the resulting road graph is too sparse.
        """
        road_types = road_types or self.DEFAULT_ROAD_TYPES
        custom_filter = self._build_filter(road_types)

        try:
            import osmnx as ox
        except ImportError as exc:
            raise CityImportError(
                CityImportErrorCode.PARSING_ERROR,
                "osmnx is not installed — run 'pip install osmnx'",
            ) from exc

        # --- Step 1: download & build graph ---
        logger.info("Downloading OSM data for '%s' …", city_name)
        try:
            G = ox.graph_from_place(
                city_name,
                network_type="drive",  # ensures we get drivable roads
                custom_filter=custom_filter,
                simplify=True,  # collapse straight-line degree-2 nodes
            )
        except ox._errors.InsufficientResponseError as exc:
            raise CityImportError(
                CityImportErrorCode.CITY_NOT_FOUND,
                f"City '{city_name}' not found in OSM. Check the spelling.",
            ) from exc
        except Exception as exc:
            msg = str(exc)
            if "timeout" in msg.lower() or "connection" in msg.lower():
                raise CityImportError(
                    CityImportErrorCode.NETWORK_ERROR,
                    f"Failed to reach OSM servers: {msg}",
                ) from exc
            raise CityImportError(
                CityImportErrorCode.PARSING_ERROR,
                f"Unexpected error during OSM download: {msg}",
            ) from exc

        # --- Step 2: convert osmnx graph → domain models ---
        node_count = G.number_of_nodes()
        edge_count = G.number_of_edges()
        logger.info(
            "OSM graph for '%s': %d nodes, %d edges", city_name, node_count, edge_count
        )

        if node_count < 5 or edge_count < 5:
            raise CityImportError(
                CityImportErrorCode.INSUFFICIENT_ROADS,
                f"Road network for '{city_name}' has only {node_count} nodes "
                f"and {edge_count} edges — too sparse for simulation.",
            )

        nodes = self._convert_nodes(G)
        edges = self._convert_edges(G)

        # --- Step 3: generate stations ---
        stations = self._generate_stations(
            G, n_stations=n_stations, eps_m=station_cluster_eps_m
        )

        # --- Step 4: build zones from OSM administrative boundaries ---
        zones = self._build_zones(city_name, ox)

        return City(nodes=nodes, edges=edges, stations=stations, zones=zones)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_filter(road_types: set[str]) -> str:
        """Build an osmnx ``custom_filter`` string from a set of highway tags."""
        tags = "|".join(sorted(road_types))
        return f'["highway"~"{tags}"]'

    @staticmethod
    def _convert_nodes(G: nx.MultiDiGraph) -> dict[str, Node]:
        """Convert osmnx graph nodes to ``Node`` domain objects."""
        nodes: dict[str, Node] = {}
        for osmid, data in G.nodes(data=True):
            node_id = str(osmid)
            lat = float(data.get("y", 0))
            lng = float(data.get("x", 0))
            elevation = float(data.get("elevation", 0.0))
            nodes[node_id] = Node(
                node_id=node_id,
                position=LatLng(lat=lat, lng=lng),
                elevation_m=elevation,
            )
        return nodes

    @staticmethod
    def _convert_edges(G: nx.MultiDiGraph) -> dict[str, Edge]:
        """Convert osmnx graph edges to ``Edge`` domain objects."""
        edges: dict[str, Edge] = {}
        for u, v, key, data in G.edges(keys=True, data=True):
            edge_id = f"{u}_{v}_{key}"
            length_m = float(data.get("length", 0))
            max_speed = float(data.get("maxspeed", 30))
            # osmnx sometimes returns a list for maxspeed
            if isinstance(max_speed, list):
                max_speed = float(max_speed[0]) if max_speed else 30.0
            edges[edge_id] = Edge(
                edge_id=edge_id,
                from_node=str(u),
                to_node=str(v),
                length_m=length_m,
                max_speed_kmh=max_speed,
            )
        return edges

    @staticmethod
    def _generate_stations(
        G: nx.MultiDiGraph,
        *,
        n_stations: int = 200,
        eps_m: float = 200.0,
    ) -> dict[str, Station]:
        """Generate stations using edge betweenness centrality + clustering.

        Strategy (Explorer's insight — functional importance > topology):
        1. Compute edge betweenness centrality for the road graph.
        2. Pick top-K edges; their endpoint nodes are station candidates.
        3. DBSCAN-cluster candidates within ``eps_m`` metres.
        4. Rank clusters by combined centrality score.
        5. Return top-*n_stations* stations.
        """
        try:
            from sklearn.cluster import DBSCAN
            import numpy as np
        except ImportError as exc:
            raise CityImportError(
                CityImportErrorCode.PARSING_ERROR,
                "scikit-learn is required for station generation: "
                "'pip install scikit-learn'",
            ) from exc

        # --- Step 3a: betweenness centrality on edges ---
        # Use a sample of 10% of nodes (min 100, max 2000) for speed
        n_total = G.number_of_nodes()
        k_sample = max(100, min(2000, n_total // 10))

        logger.info(
            "Computing edge betweenness centrality (k=%d / %d nodes) …",
            k_sample,
            n_total,
        )
        try:
            cent = nx.edge_betweenness_centrality(G, k=k_sample, seed=42)
        except ZeroDivisionError:
            # Degenerate graph — fall back to uniform centrality
            cent = {e: 1.0 for e in G.edges(keys=False)}

        # --- Step 3b: pick top edges & collect candidate node positions ---
        sorted_edges = sorted(cent.items(), key=lambda x: x[1], reverse=True)
        top_n_candidates = min(len(sorted_edges), n_stations * 3)
        top_edges = sorted_edges[:top_n_candidates]

        candidate_positions: list[tuple[float, float, str, float]] = []
        for (u, v), score in top_edges:
            for node_id in (u, v):
                data = G.nodes[node_id]
                candidate_positions.append(
                    (
                        float(data["y"]),
                        float(data["x"]),
                        str(node_id),
                        score,
                    )
                )

        if not candidate_positions:
            return {}

        # --- Step 3c: DBSCAN cluster by lat/lng ---
        coords = np.array([[lat, lng] for lat, lng, _, _ in candidate_positions])

        # Convert eps from metres to degrees (approximate: 1° ≈ 111_000 m)
        eps_deg = eps_m / 111_000.0

        clustering = DBSCAN(eps=eps_deg, min_samples=1).fit(coords)
        labels = clustering.labels_

        # --- Step 3d: aggregate clusters ---
        clusters: dict[int, list[tuple[float, float, str, float]]] = {}
        for label, pos in zip(labels, candidate_positions):
            clusters.setdefault(label, []).append(pos)

        # Score each cluster by max centrality of its members
        cluster_scores: list[tuple[int, float, float, float]] = []  # (label, score, lat, lng)
        for label, members in clusters.items():
            max_score = max(m[3] for m in members)
            # Cluster centre = arithmetic mean of member positions
            avg_lat = sum(m[0] for m in members) / len(members)
            avg_lng = sum(m[1] for m in members) / len(members)
            cluster_scores.append((label, max_score, avg_lat, avg_lng))

        # --- Step 3e: pick top-N stations ---
        cluster_scores.sort(key=lambda x: x[1], reverse=True)
        top_clusters = cluster_scores[:n_stations]

        stations: dict[str, Station] = {}
        for i, (label, score, lat, lng) in enumerate(top_clusters):
            station_id = f"s{i:04d}"
            stations[station_id] = Station(
                station_id=station_id,
                position=LatLng(lat=lat, lng=lng),
                capacity=30,  # default capacity; phase-2 may tune per POI
                name=f"Station-{i+1:04d}",
            )

        logger.info(
            "Generated %d stations from %d clusters (top %d of %d candidates)",
            len(stations),
            len(clusters),
            n_stations,
            len(candidate_positions),
        )
        return stations

    @staticmethod
    def _build_zones(city_name: str, ox: Any) -> dict[str, Zone]:
        """Build zones from OSM administrative boundary.

        Uses ``osmnx.geometries_from_place()`` with ``admin_level=8``
        (city district) or ``admin_level=9`` (sub-district).
        Falls back to a single catch-all zone with the city boundary.
        """
        try:
            import geopandas as gpd
        except ImportError:
            # geopandas is an optional extra; fall back gracefully
            return _fallback_zone(city_name)

        try:
            gdf = ox.geometries_from_place(
                city_name,
                tags={"boundary": "administrative", "admin_level": ["8", "9"]},
            )
        except Exception:
            logger.warning("Failed to load administrative boundaries for '%s'", city_name)
            return _fallback_zone(city_name)

        if gdf.empty:
            return _fallback_zone(city_name)

        zones: dict[str, Zone] = {}
        for idx, row in gdf.iterrows():
            zone_id = f"z{idx}" if not isinstance(idx, int) else f"z{idx:04d}"
            name = row.get("name", f"Zone-{zone_id}")
            polygon = _extract_polygon(row.geometry)
            if polygon:
                zones[zone_id] = Zone(zone_id=zone_id, name=name, polygon=polygon)

        if not zones:
            return _fallback_zone(city_name)

        logger.info("Loaded %d administrative zones for '%s'", len(zones), city_name)
        return zones


# ------------------------------------------------------------------
# Module-level helpers (also used by tests)
# ------------------------------------------------------------------


def _fallback_zone(city_name: str) -> dict[str, Zone]:
    """Return a single generic zone when admin boundaries are unavailable."""
    return {
        "z0000": Zone(
            zone_id="z0000",
            name=city_name,
            polygon=[],
        )
    }


def _extract_polygon(geometry: Any) -> list[LatLng]:
    """Extract a flat list of LatLng vertices from a shapely geometry."""
    try:
        if geometry.geom_type == "Polygon":
            coords = list(geometry.exterior.coords)
            return [LatLng(lat=y, lng=x) for x, y in coords]
        if geometry.geom_type == "MultiPolygon":
            # Take the largest polygon by area
            poly = max(geometry.geoms, key=lambda p: p.area)
            coords = list(poly.exterior.coords)
            return [LatLng(lat=y, lng=x) for x, y in coords]
    except Exception:
        logger.exception("Failed to extract polygon from geometry")
    return []
