"""Map service — loads and caches City from OSM data."""

from __future__ import annotations

import random
from math import cos, radians

from app.core.city import City, LatLng, Node, Edge, Station, Zone, _haversine_km

# Beijing bounding box (approximate)
_BEIJING_BBOX = {
    "lat_min": 39.75,
    "lat_max": 40.05,
    "lng_min": 116.15,
    "lng_max": 116.60,
}


class MapService:
    """Service responsible for loading city map data."""

    _cache: dict[str, City] = {}

    def load_city(self, city_name: str) -> City:
        """Load or build a City from map data.

        Phase 1: synthetic grid city for integration testing.
        Phase 2+: real OSM parsing via osmium / osmnx.
        """
        if city_name in self._cache:
            return self._cache[city_name]

        if city_name.lower() == "beijing":
            city = self._build_synthetic_beijing()
        else:
            city = self._build_minimal_city(city_name)

        self._cache[city_name] = city
        return city

    def _build_synthetic_beijing(self) -> City:
        """Build a realistic synthetic grid city approximating Beijing.

        Uses a 35x35 grid → ~1225 nodes, ~2380 directed edges, > 200 stations.
        All values are deterministic (seed set for reproducibility).
        """
        random.seed(42)

        lat_min = _BEIJING_BBOX["lat_min"]
        lat_max = _BEIJING_BBOX["lat_max"]
        lng_min = _BEIJING_BBOX["lng_min"]
        lng_max = _BEIJING_BBOX["lng_max"]

        grid_rows = 35
        grid_cols = 35

        dlat = (lat_max - lat_min) / (grid_rows - 1)
        dlng = (lng_max - lng_min) / (grid_cols - 1)

        # --- Generate nodes ---
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

        # --- Generate edges (bidirectional) ---
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
                    edges[f"e_{edge_id}"] = Edge(
                        edge_id=f"e_{edge_id}",
                        from_node=nid,
                        to_node=nid_r,
                        length_m=round(dist, 1),
                        max_speed_kmh=40.0,
                    )
                    edge_id += 1
                    # Return edge
                    edges[f"e_{edge_id}"] = Edge(
                        edge_id=f"e_{edge_id}",
                        from_node=nid_r,
                        to_node=nid,
                        length_m=round(dist, 1),
                        max_speed_kmh=40.0,
                    )
                    edge_id += 1
                # Vertical edge (down)
                if r + 1 < grid_rows:
                    nid_d = f"n_{r+1}_{c}"
                    pos_d = nodes[nid_d].position
                    dist = _haversine_km(pos, pos_d) * 1000
                    edges[f"e_{edge_id}"] = Edge(
                        edge_id=f"e_{edge_id}",
                        from_node=nid,
                        to_node=nid_d,
                        length_m=round(dist, 1),
                        max_speed_kmh=40.0,
                    )
                    edge_id += 1
                    # Return edge
                    edges[f"e_{edge_id}"] = Edge(
                        edge_id=f"e_{edge_id}",
                        from_node=nid_d,
                        to_node=nid,
                        length_m=round(dist, 1),
                        max_speed_kmh=40.0,
                    )
                    edge_id += 1

        # --- Generate stations (every 2nd node in both directions) ---
        stations: dict[str, Station] = {}
        station_id = 0
        station_names = [
            "国贸", "西单", "王府井", "中关村", "五道口",
            "望京", "三里屯", "朝阳门", "东直门", "西直门",
            "海淀黄庄", "苏州街", "知春路", "大望路", "双井",
            "呼家楼", "金台夕照", "亮马桥", "农业展览馆", "团结湖",
        ]
        for r in range(0, grid_rows, 2):
            for c in range(0, grid_cols, 2):
                nid = f"n_{r}_{c}"
                pos = nodes[nid].position
                name = station_names[station_id % len(station_names)]
                if station_id // len(station_names) > 0:
                    name = f"{name}{station_id // len(station_names)}"
                stations[f"s_{station_id}"] = Station(
                    station_id=f"s_{station_id}",
                    position=pos,
                    capacity=random.choice([20, 30, 40, 50]),
                    name=name,
                )
                station_id += 1

        # --- Zones (2x2 grid of operational districts) ---
        zones: dict[str, Zone] = {}
        zone_names = ["海淀", "朝阳", "东城", "西城"]
        for zid, zname in enumerate(zone_names):
            r_start = (zid // 2) * (grid_rows // 2)
            r_end = r_start + grid_rows // 2
            c_start = (zid % 2) * (grid_cols // 2)
            c_end = c_start + grid_cols // 2
            corners = [
                nodes[f"n_{r_start}_{c_start}"].position,
                nodes[f"n_{r_start}_{c_end - 1}"].position,
                nodes[f"n_{r_end - 1}_{c_end - 1}"].position,
                nodes[f"n_{r_end - 1}_{c_start}"].position,
            ]
            zones[f"z_{zid}"] = Zone(
                zone_id=f"z_{zid}",
                name=zname,
                polygon=corners,
            )

        return City(nodes=nodes, edges=edges, stations=stations, zones=zones)

    def _build_minimal_city(self, name: str) -> City:
        """Return a minimal single-node city for unknown city names."""
        center = LatLng(lat=39.9042, lng=116.4074)
        nodes = {"n1": Node(node_id="n1", position=center)}
        return City(nodes=nodes, edges={}, stations={}, zones={})

    def clear_cache(self) -> None:
        """Clear the in-memory city cache."""
        self._cache.clear()
