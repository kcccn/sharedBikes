"""Map service — loads and caches City from OSM data.

Supports a layered loading strategy:
1.  Load **CityConfig** from a TOML file (via ``CityLoader``).
2.  Build a synthetic road network for mock mode, or parse real OSM data.
3.  Auto-generate stations on the network (via ``station_generator``).
4.  Cache the built ``City`` for the lifetime of the process.
"""

from __future__ import annotations

import math
from pathlib import Path

from app.core.city import City, Edge, LatLng, Node, Station, Zone
from app.core.city_config import CityConfig
from app.core.station_generator import generate_stations
from app.services.city_loader import CityLoader, CityLoadError
from app.services.osm_parser import OSMError, parse_from_bbox, parse_from_file, parse_from_place


class MapService:
    """Service responsible for loading city map data."""

    def __init__(
        self,
        loader: CityLoader | None = None,
        data_dir: str | Path = "data",
    ) -> None:
        self._loader = loader or CityLoader(config_dir=Path(data_dir) / "cities")
        self._cache: dict[str, City] = {}

    # ── Public API ───────────────────────────────────────────────────

    def list_available_cities(self) -> list[str]:
        """Return city IDs for which configuration exists."""
        return self._loader.list_available_cities()

    def load_city(self, city_id: str) -> City:
        """Load (or return cached) City for *city_id*.

        1. Try loading from TOML config (config-driven pipeline).
        2. Fallback: try OSM place-name lookup (e.g. ``"Beijing, China"``).
        3. Last resort: return a minimal synthetic city (never crashes).
        """
        if city_id in self._cache:
            return self._cache[city_id]

        # Strategy 1: Config-driven pipeline
        try:
            config = self._loader.load(city_id)
            city = self._build_city(config)
            self._cache[city_id] = city
            return city
        except CityLoadError:
            pass

        # Strategy 2: OSM place-name lookup
        try:
            city = parse_from_place(city_id)
            self._cache[city_id] = city
            return city
        except OSMError:
            pass

        # Strategy 3: Minimal fallback
        city = self._build_minimal_city(city_id)
        self._cache[city_id] = city
        return city

    def load_from_bbox(
        self,
        north: float,
        south: float,
        east: float,
        west: float,
    ) -> City:
        """Load a City from a bounding box via OSM."""
        return parse_from_bbox(north=north, south=south, east=east, west=west)

    def load_from_file(self, filepath: str | Path) -> City:
        """Load a City from a local ``.osm.pbf`` or ``.osm`` file."""
        return parse_from_file(filepath)

    # ── Config-driven pipeline ───────────────────────────────────────

    def _build_city(self, config: CityConfig) -> City:
        """Construct a ``City`` from its configuration."""
        nodes, edges = self._load_road_network(config)

        stations: dict[str, Station] = {}
        if config.station_generation.enabled:
            stations = generate_stations(
                nodes,
                edges,
                min_distance_km=config.station_generation.min_distance_km,
                min_capacity=config.station_generation.min_capacity,
                max_capacity=config.station_generation.max_capacity,
                max_stations=config.station_generation.max_stations,
            )

        zones: dict[str, Zone] = self._build_zones(config)
        return City(nodes=nodes, edges=edges, stations=stations, zones=zones)

    def _load_road_network(
        self, config: CityConfig
    ) -> tuple[dict[str, Node], dict[str, Edge]]:
        """Parse road network based on the configured OSM source."""
        if config.osm.source == "mock":
            return self._build_synthetic_grid(config)
        # Phase 2+: delegate to real OSM parsing
        if config.osm.source == "url" and config.osm.bounding_box:
            bbox = config.osm.bounding_box
            try:
                city = parse_from_bbox(
                    north=bbox[2], south=bbox[0], east=bbox[3], west=bbox[1]
                )
                return city.nodes, city.edges
            except OSMError:
                pass
        if config.osm.source == "file" and config.osm.file_path:
            try:
                city = parse_from_file(config.osm.file_path)
                return city.nodes, city.edges
            except OSMError:
                pass
        # Fallback
        return self._build_synthetic_grid(config)

    @staticmethod
    def _build_synthetic_grid(
        config: CityConfig,
    ) -> tuple[dict[str, Node], dict[str, Edge]]:
        """Build a synthetic grid road network approximating the city area.

        Defaults to a Beijing-scale 35×35 grid when no bounding box is set.
        """
        # Determine bounding box
        if config.osm.bounding_box:
            lat_min, lng_min, lat_max, lng_max = config.osm.bounding_box
        else:
            lat_min, lng_min, lat_max, lng_max = 39.75, 116.15, 40.05, 116.60

        grid_rows = 35
        grid_cols = 35
        dlat = (lat_max - lat_min) / (grid_rows - 1)
        dlng = (lng_max - lng_min) / (grid_cols - 1)

        # Generate nodes
        import random

        random.seed(42)  # deterministic for reproducibility
        nodes: dict[str, Node] = {}
        for r in range(grid_rows):
            for c in range(grid_cols):
                node_id = f"n_{r}_{c}"
                lat = lat_min + r * dlat + random.uniform(-0.0005, 0.0005)
                lng = lng_min + c * dlng + random.uniform(-0.0005, 0.0005)
                elev = random.uniform(10, 80)
                nodes[node_id] = Node(
                    node_id=node_id,
                    position=LatLng(lat=round(lat, 6), lng=round(lng, 6)),
                    elevation_m=round(elev, 1),
                )

        # Generate edges (bidirectional)
        edges: dict[str, Edge] = {}
        edge_id = 0
        for r in range(grid_rows):
            for c in range(grid_cols):
                nid = f"n_{r}_{c}"
                pos = nodes[nid].position
                # Horizontal edge (right)
                if c + 1 < grid_cols:
                    nid_r = f"n_{r}_{c+1}"
                    pos_r = nodes[nid_r].position
                    dist = _haversine_km(pos, pos_r) * 1000
                    for direction in [(nid, nid_r), (nid_r, nid)]:
                        edges[f"e_{edge_id}"] = Edge(
                            edge_id=f"e_{edge_id}",
                            from_node=direction[0],
                            to_node=direction[1],
                            length_m=round(dist, 1),
                            max_speed_kmh=40.0,
                        )
                        edge_id += 1
                # Vertical edge (down)
                if r + 1 < grid_rows:
                    nid_d = f"n_{r+1}_{c}"
                    pos_d = nodes[nid_d].position
                    dist = _haversine_km(pos, pos_d) * 1000
                    for direction in [(nid, nid_d), (nid_d, nid)]:
                        edges[f"e_{edge_id}"] = Edge(
                            edge_id=f"e_{edge_id}",
                            from_node=direction[0],
                            to_node=direction[1],
                            length_m=round(dist, 1),
                            max_speed_kmh=40.0,
                        )
                        edge_id += 1
        return nodes, edges

    @staticmethod
    def _build_zones(config: CityConfig) -> dict[str, Zone]:
        """Build zones from config or return an empty dict."""
        zones: dict[str, Zone] = {}
        for zc in config.zone_configs:
            polygon = [LatLng(p["lat"], p["lng"]) for p in zc.get("polygon", [])]
            zones[zc["zone_id"]] = Zone(
                zone_id=zc["zone_id"],
                name=zc.get("name", zc["zone_id"]),
                polygon=polygon,
            )
        return zones

    # ── Fallback ─────────────────────────────────────────────────────

    @staticmethod
    def _build_minimal_city(name: str) -> City:
        """Return a minimal City with a single node (used as last resort)."""
        center = LatLng(lat=39.9042, lng=116.4074)
        nodes = {"n1": Node(node_id="n1", position=center)}
        return City(nodes=nodes, edges={}, stations={}, zones={})

    # ── Cache control ────────────────────────────────────────────────

    def clear_cache(self) -> None:
        """Invalidate the in-memory city cache."""
        self._cache.clear()


# ── Internal helper ─────────────────────────────────────────────────


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
