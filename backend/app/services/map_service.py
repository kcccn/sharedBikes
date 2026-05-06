"""Map service — loads and caches City from OSM data.

Supports a layered loading strategy:
1.  Load **CityConfig** from a TOML file (via ``CityLoader``).
2.  Parse OSM data according to the config (mock → real later).
3.  Auto-generate stations on the road network.
4.  Cache the built ``City`` for the lifetime of the process.
"""

from __future__ import annotations

from pathlib import Path

from app.core.city import City, Edge, LatLng, Node, Station, Zone
from app.core.city_config import CityConfig
from app.core.station_generator import generate_stations
from app.services.city_loader import CityLoader, CityLoadError


class MapService:
    """Service responsible for loading city map data."""

    def __init__(
        self,
        loader: CityLoader | None = None,
        data_dir: str | Path = "data",
    ) -> None:
        self._loader = loader or CityLoader(config_dir=Path(data_dir) / "cities")
        self._cache: dict[str, City] = {}

    def list_available_cities(self) -> list[str]:
        """Return city IDs for which configuration exists."""
        return self._loader.list_available_cities()

    def load_city(self, city_id: str) -> City:
        """Load (or return cached) City for *city_id*.

        Parameters
        ----------
        city_id:
            Identifier matching a ``{city_id}.toml`` config file.

        Raises
        ------
        CityLoadError
            If no config or OSM data is available for the given ID.
        """
        if city_id in self._cache:
            return self._cache[city_id]

        config = self._loader.load(city_id)
        city = self._build_city(config)
        self._cache[city_id] = city
        return city

    def _build_city(self, config: CityConfig) -> City:
        """Construct a ``City`` from its configuration."""

        # Phase 1: mock data — a few nodes around the city centre.
        # Phase 2+: real OSM parsing from the configured source.
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

    @staticmethod
    def _load_road_network(
        config: CityConfig,
    ) -> tuple[dict[str, Node], dict[str, Edge]]:
        """Parse road network from the configured OSM source.

        Phase 1: return a minimal mock grid.
        Phase 2+: delegate to an OSM parser (osmium / osmnx).
        """
        _ = config  # placeholder — will be used in Phase 2
        # A 3×3 grid of nodes for basic testing
        base_lat, base_lng = 39.9042, 116.4074  # Beijing centre
        nodes: dict[str, Node] = {}
        edges: dict[str, Edge] = {}
        for row in range(3):
            for col in range(3):
                nid = f"n{row}_{col}"
                nodes[nid] = Node(
                    node_id=nid,
                    position=LatLng(
                        lat=base_lat + row * 0.02,
                        lng=base_lng + col * 0.02,
                    ),
                )
        # Horizontal edges
        for row in range(3):
            for col in range(2):
                frm = f"n{row}_{col}"
                to = f"n{row}_{col + 1}"
                eid = f"e{row}_{col}_h"
                edges[eid] = Edge(
                    edge_id=eid, from_node=frm, to_node=to, length_m=2000
                )
        # Vertical edges
        for col in range(3):
            for row in range(2):
                frm = f"n{row}_{col}"
                to = f"n{row + 1}_{col}"
                eid = f"e{row}_{col}_v"
                edges[eid] = Edge(
                    edge_id=eid, from_node=frm, to_node=to, length_m=2200
                )
        return nodes, edges

    @staticmethod
    def _build_zones(config: CityConfig) -> dict[str, Zone]:
        """Build zones from config or return an empty dict."""
        zones: dict[str, Zone] = {}
        for zc in config.zone_configs:
            polygon = [
                LatLng(p["lat"], p["lng"]) for p in zc.get("polygon", [])
            ]
            zones[zc["zone_id"]] = Zone(
                zone_id=zc["zone_id"],
                name=zc.get("name", zc["zone_id"]),
                polygon=polygon,
            )
        return zones

    def clear_cache(self) -> None:
        """Invalidate the in-memory city cache."""
        self._cache.clear()
