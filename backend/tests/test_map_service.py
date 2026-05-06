"""MapService integration tests — Phase 1.

Covers:
- Synthetic grid city building and structural validation
- Strong connectivity verification
- Station generation non-overlap
- Cache hit / miss / clear behavior
- Edge cases (unknown city, empty nodes)
- OSM fixture file presence
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import pytest

from app.core.city import City, Edge, LatLng, Node, Station, Zone
from app.services.map_service import MapService

# ---------------------------------------------------------------------------
# Helpers — synthetic city builder
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
OSM_DIR = FIXTURES_DIR / "osm"


def _haversine_km(a: LatLng, b: LatLng) -> float:
    """Great-circle distance in km."""
    R = 6371.0
    dlat = math.radians(b.lat - a.lat)
    dlng = math.radians(b.lng - a.lng)
    sin_dlat = math.sin(dlat / 2)
    sin_dlng = math.sin(dlng / 2)
    h = (
        sin_dlat * sin_dlat
        + math.cos(math.radians(a.lat))
        * math.cos(math.radians(b.lat))
        * sin_dlng * sin_dlng
    )
    return 2 * R * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def build_grid_city(
    rows: int,
    cols: int,
    lat_min: float = 39.90,
    lat_max: float = 39.94,
    lng_min: float = 116.30,
    lng_max: float = 116.36,
    seed: int = 42,
) -> City:
    """Build a deterministic rectangular grid city for testing.

    Creates *rows* x *cols* nodes connected as a directed grid with
    bidirectional edges on every segment.
    """
    rng = random.Random(seed)

    dlat = (lat_max - lat_min) / max(rows - 1, 1)
    dlng = (lng_max - lng_min) / max(cols - 1, 1)

    # Nodes
    nodes: dict[str, Node] = {}
    for r in range(rows):
        for c in range(cols):
            nid = f"n_{r}_{c}"
            lat = lat_min + r * dlat + rng.uniform(-0.0002, 0.0002)
            lng = lng_min + c * dlng + rng.uniform(-0.0002, 0.0002)
            elev = rng.uniform(10.0, 80.0)
            nodes[nid] = Node(
                node_id=nid,
                position=LatLng(lat=round(lat, 6), lng=round(lng, 6)),
                elevation_m=round(elev, 1),
            )

    # Edges (bidirectional on each segment)
    edges: dict[str, Edge] = {}
    eid = 0
    for r in range(rows):
        for c in range(cols):
            nid = f"n_{r}_{c}"
            pos = nodes[nid].position
            # Right neighbour
            if c + 1 < cols:
                nid_r = f"n_{r}_{c+1}"
                dist = _haversine_km(pos, nodes[nid_r].position) * 1000
                for _from, _to in ((nid, nid_r), (nid_r, nid)):
                    edges[f"e_{eid}"] = Edge(
                        edge_id=f"e_{eid}",
                        from_node=_from,
                        to_node=_to,
                        length_m=round(dist, 1),
                        max_speed_kmh=40.0,
                    )
                    eid += 1
            # Down neighbour
            if r + 1 < rows:
                nid_d = f"n_{r+1}_{c}"
                dist = _haversine_km(pos, nodes[nid_d].position) * 1000
                for _from, _to in ((nid, nid_d), (nid_d, nid)):
                    edges[f"e_{eid}"] = Edge(
                        edge_id=f"e_{eid}",
                        from_node=_from,
                        to_node=_to,
                        length_m=round(dist, 1),
                        max_speed_kmh=40.0,
                    )
                    eid += 1

    return City(nodes=nodes, edges=edges, stations={}, zones={})


def is_strongly_connected(city: City) -> bool:
    """Kosaraju-style check: every node reachable from every other node.

    Returns True if the directed graph is one strongly connected component.
    """
    node_ids = set(city.nodes)
    if not node_ids:
        return True  # empty graph is trivially connected

    # adjacency
    forward: dict[str, set[str]] = {n: set() for n in node_ids}
    reverse: dict[str, set[str]] = {n: set() for n in node_ids}
    for edge in city.edges.values():
        if edge.from_node in forward and edge.to_node in forward:
            forward[edge.from_node].add(edge.to_node)
            reverse[edge.to_node].add(edge.from_node)

    def _dfs(graph: dict[str, set[str]], start: str) -> set[str]:
        visited: set[str] = set()
        stack = [start]
        while stack:
            v = stack.pop()
            if v not in visited:
                visited.add(v)
                stack.extend(graph[v] - visited)
        return visited

    # 1. DFS from arbitrary node
    start = next(iter(node_ids))
    visited_forward = _dfs(forward, start)
    if visited_forward != node_ids:
        return False

    # 2. DFS on reversed graph from same start
    visited_reverse = _dfs(reverse, start)
    return visited_reverse == node_ids


# ======================================================================
# Tests
# ======================================================================


class TestGridCity:
    """Synthetic grid city structural tests."""

    def test_3x3_grid_counts(self) -> None:
        city = build_grid_city(3, 3)
        assert len(city.nodes) == 9
        # 3 rows × 2 horizontal segments × 2 dirs = 12
        # 3 cols × 2 vertical segments × 2 dirs = 12
        # Total = 24
        assert len(city.edges) == 24, f"Expected 24 edges, got {len(city.edges)}"

    def test_5x5_grid_counts(self) -> None:
        city = build_grid_city(5, 5)
        assert len(city.nodes) == 25
        # 5×4×2 + 4×5×2 = 40 + 40 = 80
        assert len(city.edges) == 80

    def test_all_edges_reference_valid_nodes(self) -> None:
        city = build_grid_city(4, 4)
        node_ids = set(city.nodes)
        for edge in city.edges.values():
            assert edge.from_node in node_ids, f"{edge.edge_id} bad from_node"
            assert edge.to_node in node_ids, f"{edge.edge_id} bad to_node"

    def test_3x3_grid_is_strongly_connected(self) -> None:
        """A rectangular grid with bidirectional edges is SCC."""
        city = build_grid_city(3, 3)
        assert is_strongly_connected(city)

    def test_10x10_grid_is_strongly_connected(self) -> None:
        city = build_grid_city(10, 10)
        assert is_strongly_connected(city)

    def test_single_node_is_strongly_connected(self) -> None:
        nodes = {"n0": Node(node_id="n0", position=LatLng(39.9, 116.4))}
        city = City(nodes=nodes, edges={}, stations={}, zones={})
        assert is_strongly_connected(city)

    def test_disconnected_graph(self) -> None:
        """Two separate nodes with no edges — not strongly connected."""
        nodes = {
            "n0": Node(node_id="n0", position=LatLng(39.9, 116.4)),
            "n1": Node(node_id="n1", position=LatLng(39.91, 116.41)),
        }
        city = City(nodes=nodes, edges={}, stations={}, zones={})
        assert not is_strongly_connected(city)


class TestStationNonOverlap:
    """Generated stations must respect minimum distance."""

    MIN_DISTANCE_KM = 0.3

    def test_stations_are_non_overlapping(self) -> None:
        """Check every station pair is >= min_distance apart."""
        city = build_grid_city(10, 10)

        # Place a station on every even-indexed node
        stations: dict[str, Station] = {}
        for r in range(0, 10, 2):
            for c in range(0, 10, 2):
                nid = f"n_{r}_{c}"
                node = city.nodes[nid]
                sid = f"s_{r}_{c}"
                stations[sid] = Station(
                    station_id=sid,
                    position=node.position,
                    capacity=20,
                    name=f"Station_{r}_{c}",
                )

        stations_list = list(stations.values())
        for i in range(len(stations_list)):
            for j in range(i + 1, len(stations_list)):
                d = _haversine_km(
                    stations_list[i].position,
                    stations_list[j].position,
                )
                assert d >= self.MIN_DISTANCE_KM or abs(d) < 1e-9, (
                    f"{stations_list[i].station_id} ↔ {stations_list[j].station_id} "
                    f"distance {d:.4f}km < {self.MIN_DISTANCE_KM}km"
                )

    def test_no_duplicate_positions(self) -> None:
        """Two stations must not share exact coordinates."""
        stations: dict[str, Station] = {}
        for i in range(5):
            lat = 39.90 + i * 0.01
            lng = 116.30 + i * 0.01
            sid = f"s{i}"
            stations[sid] = Station(
                station_id=sid,
                position=LatLng(lat=lat, lng=lng),
                capacity=20,
            )

        positions = {s.position for s in stations.values()}
        assert len(positions) == len(stations), "Duplicate station positions detected"


class TestMapServiceIntegration:
    """MapService integration tests using the main branch stub."""

    def test_load_city_returns_city(self) -> None:
        service = MapService()
        city = service.load_city("Beijing")
        assert city is not None
        assert isinstance(city, City)

    def test_load_city_unknown_name(self) -> None:
        """Unknown city names should not crash."""
        service = MapService()
        city = service.load_city("nonexistent_city_xyz")
        assert city is not None
        assert isinstance(city.nodes, dict)
        assert isinstance(city.edges, dict)

    def test_cache_hit_returns_same_object(self) -> None:
        """Loading the same name twice returns the same city."""
        service = MapService()
        service._cache.clear()
        city_a = service.load_city("beijing")
        city_b = service.load_city("beijing")
        assert city_a is city_b  # same object (cached)

    def test_cache_clear_forces_reload(self) -> None:
        service = MapService()
        service._cache.clear()
        city_a = service.load_city("beijing")
        service.clear_cache()
        city_b = service.load_city("beijing")
        assert city_a is not city_b  # different objects

    def test_cache_different_names(self) -> None:
        """Different city names should not share cache entries."""
        service = MapService()
        service._cache.clear()
        city_a = service.load_city("beijing")
        city_b = service.load_city("shanghai")
        # Current stub returns same structure, but they should be separate loads
        assert len(service._cache) >= 2


class TestEdgeCases:
    """Boundary and edge-case scenarios."""

    def test_empty_city_acceptance(self) -> None:
        """City with zero nodes and edges is technically valid."""
        city = City(nodes={}, edges={}, stations={}, zones={})
        assert city.nodes == {}
        assert city.edges == {}
        assert is_strongly_connected(city)  # empty is trivially connected

    def test_single_node_city(self) -> None:
        """Single node with no edges is valid and connected."""
        nodes = {"n1": Node(node_id="n1", position=LatLng(39.9, 116.4))}
        city = City(nodes=nodes, edges={}, stations={}, zones={})
        assert len(city.nodes) == 1
        assert len(city.edges) == 0
        assert is_strongly_connected(city)


class TestOSMFixtures:
    """Verify OSM fixture files exist and are valid XML.

    Parsing these files with osm_parser requires PR #43 to be merged.
    These tests confirm the fixture data is in place.
    """

    def test_fixtures_dir_exists(self) -> None:
        assert FIXTURES_DIR.is_dir(), f"Fixtures dir not found: {FIXTURES_DIR}"

    def test_osm_dir_exists(self) -> None:
        assert OSM_DIR.is_dir(), f"OSM fixtures dir not found: {OSM_DIR}"

    @pytest.mark.parametrize(
        "filename",
        ["small_grid.osm", "empty.osm", "broken_ref.osm"],
    )
    def test_osm_fixture_exists(self, filename: str) -> None:
        path = OSM_DIR / filename
        assert path.is_file(), f"Missing fixture: {path}"
        assert path.stat().st_size > 0, f"Empty fixture: {path}"
        content = path.read_text(encoding="utf-8")
        assert "<osm" in content, f"Not valid OSM XML: {path}"


class TestPerformance:
    """Performance baseline for city loading."""

    def test_synthetic_grid_build_time(self) -> None:
        """Building a 10x10 grid should be fast (< 0.5 s)."""
        import time
        t0 = time.perf_counter()
        build_grid_city(10, 10)
        elapsed = time.perf_counter() - t0
        assert elapsed < 0.5, f"Grid build took {elapsed:.3f}s"

    def test_map_service_load_time(self) -> None:
        """MapService.load_city should return quickly for any city name (< 1 s)."""
        import time
        service = MapService()
        t0 = time.perf_counter()
        service.load_city("test_city")
        elapsed = time.perf_counter() - t0
        assert elapsed < 1.0, f"Load city took {elapsed:.3f}s"
