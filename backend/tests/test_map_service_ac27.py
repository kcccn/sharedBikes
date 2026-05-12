"""Issue #27 acceptance criteria: connectivity, non-overlap, boundary cases.

These tests cover the missing AC items not yet present in
test_phase1_integration.py or test_map_service.py:

  AC3  Strong connectivity -- Kosaraju verification
  AC4  Station position non-overlap -- min-distance constraint
  AC5  Boundary cases -- empty city, single node, broken edge refs

All position calculations use Euclidean distance on Coord(x, y).
"""

from __future__ import annotations

import itertools
import math

from app.core.city import Coord, Node, Edge, Station
from app.core.station_generator import generate_stations


# =========================================================================
# AC3 -- Strong Connectivity (Kosaraju's algorithm)
# =========================================================================


def _build_adjacency(edges: dict[str, Edge]) -> dict[str, set[str]]:
    """Build adjacency list from edges (directed)."""
    adj: dict[str, set[str]] = {}
    for e in edges.values():
        adj.setdefault(e.from_node, set()).add(e.to_node)
        adj.setdefault(e.to_node, set())  # ensure key exists
    return adj


def _build_reverse_adj(edges: dict[str, Edge]) -> dict[str, set[str]]:
    """Build reverse adjacency list (transposed graph)."""
    radj: dict[str, set[str]] = {}
    for e in edges.values():
        radj.setdefault(e.to_node, set()).add(e.from_node)
        radj.setdefault(e.from_node, set())  # ensure key exists
    return radj


def _kosaraju_scc_count(edges: dict[str, Edge]) -> int:
    """Return the number of strongly connected components (Kosaraju's algorithm).

    A fully strongly connected graph has 1 SCC.
    """
    radj = _build_reverse_adj(edges)
    adj = _build_adjacency(edges)

    all_nodes = set(adj.keys()) | set(radj.keys())
    if not all_nodes:
        return 0

    visited: set[str] = set()
    order: list[str] = []

    # First DFS pass: record finishing order
    def dfs(v: str) -> None:
        visited.add(v)
        for nb in adj.get(v, set()):
            if nb not in visited:
                dfs(nb)
        order.append(v)

    for v in all_nodes:
        if v not in visited:
            dfs(v)

    # Second DFS pass on reversed graph
    visited.clear()
    scc_count = 0

    def rdfs(v: str) -> None:
        visited.add(v)
        for nb in radj.get(v, set()):
            if nb not in visited:
                rdfs(nb)

    for v in reversed(order):
        if v not in visited:
            rdfs(v)
            scc_count += 1

    return scc_count


def test_connectivity_3x3_grid_is_fully_connected() -> None:
    """AC3: A 3x3 grid with bidirectional edges must be 1 SCC."""
    nodes, edges = _build_3x3_grid()
    scc_count = _kosaraju_scc_count(edges)
    assert scc_count == 1, (
        f"Expected 1 SCC for fully connected 3x3 grid, got {scc_count}"
    )


def test_connectivity_disconnected_graph() -> None:
    """AC3: Two isolated subgraphs must yield 2 SCCs."""
    edges: dict[str, Edge] = {
        "e1": Edge(edge_id="e1", from_node="a", to_node="b", length_m=100),
        "e2": Edge(edge_id="e2", from_node="c", to_node="d", length_m=100),
    }
    scc_count = _kosaraju_scc_count(edges)
    assert scc_count == 2


def test_connectivity_empty_edges() -> None:
    """AC3: An empty edge set has 0 SCCs (no graph)."""
    edges: dict[str, Edge] = {}
    scc_count = _kosaraju_scc_count(edges)
    assert scc_count == 0


def test_connectivity_directed_ring() -> None:
    """AC3: A directed cycle is strongly connected (1 SCC)."""
    edges: dict[str, Edge] = {
        "e1": Edge(edge_id="e1", from_node="a", to_node="b", length_m=100),
        "e2": Edge(edge_id="e2", from_node="b", to_node="c", length_m=100),
        "e3": Edge(edge_id="e3", from_node="c", to_node="a", length_m=100),
    }
    scc_count = _kosaraju_scc_count(edges)
    assert scc_count == 1


# =========================================================================
# AC4 -- Station Position Non-Overlap (minimum distance constraint)
# =========================================================================


def _check_station_min_distance(
    stations: dict[str, Station],
    min_dist: float,
) -> list[tuple[str, str, float]]:
    """Return list of (station_a, station_b, distance) pairs that violate the min-distance constraint."""
    violations: list[tuple[str, str, float]] = []
    items = list(stations.items())
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            sid_a, sta = items[i]
            sid_b, stb = items[j]
            d = sta.position.distance_to(stb.position)
            if d < min_dist:
                violations.append((sid_a, sid_b, d))
    return violations


def test_stations_no_overlap_3x3_grid() -> None:
    """AC4: Stations generated on a 3x3 grid must respect min_distance."""
    nodes, edges = _build_3x3_grid()
    min_dist = 0.3
    stations = generate_stations(
        nodes, edges, min_distance=min_dist, min_capacity=10, max_capacity=50
    )
    assert len(stations) > 0, "Should generate at least 1 station"

    violations = _check_station_min_distance(stations, min_dist)
    assert not violations, (
        f"Found {len(violations)} station pair(s) below {min_dist}: "
        + ", ".join(f"{a}<->{b}={d:.4f}" for a, b, d in violations)
    )


def test_stations_tight_min_distance_allows_more() -> None:
    """AC4: Smaller min_distance allows more stations."""
    nodes, edges = _build_3x3_grid()
    relaxed = generate_stations(nodes, edges, min_distance=0.01, min_capacity=10, max_capacity=50)
    strict = generate_stations(nodes, edges, min_distance=0.5, min_capacity=10, max_capacity=50)
    assert len(relaxed) >= len(strict), (
        f"Relaxed ({len(relaxed)}) should have >= stations than strict ({len(strict)})"
    )


# =========================================================================
# AC5 -- Boundary Cases
# =========================================================================


def test_empty_city_returns_no_stations() -> None:
    """AC5: Empty nodes/edges must produce zero stations."""
    stations = generate_stations({}, {}, min_capacity=10, max_capacity=50)
    assert stations == {}


def test_single_node_no_edges_returns_fallback() -> None:
    """AC5: A city with one node and no edges falls back to grid placement."""
    nodes = {
        "n1": Node(node_id="n1", position=Coord(0.0, 0.0)),
    }
    stations = generate_stations(nodes, {}, min_capacity=10, max_capacity=50)
    # The grid fallback should place 1 station on the single node
    assert len(stations) == 1
    assert "station-auto-n1" in stations


def test_single_node_no_edges_max_stations_zero() -> None:
    """AC5: Single node with max_stations=0 or similar limit."""
    nodes = {
        "n1": Node(node_id="n1", position=Coord(0.0, 0.0)),
    }
    stations = generate_stations(nodes, {}, min_capacity=10, max_capacity=50, max_stations=0)
    assert len(stations) == 0


def test_broken_edge_refers_to_missing_node() -> None:
    """AC5: generate_stations must not crash if an edge refs a non-existent node
    and must still produce a station for the valid node."""
    nodes = {
        "n1": Node(node_id="n1", position=Coord(0.0, 0.0)),
    }
    edges = {
        "e_broken": Edge(
            edge_id="e_broken",
            from_node="n1",
            to_node="ghost_node",
            length_m=100,
        ),
    }
    # Must not raise KeyError, and valid node n1 should still get a station
    stations = generate_stations(nodes, edges, min_capacity=10, max_capacity=50)
    assert isinstance(stations, dict)
    assert len(stations) > 0, "Should produce at least 1 station from valid node n1"
    station_ids = list(stations.keys())
    assert any("n1" in sid for sid in station_ids), (
        f"Expected a station near n1, got: {station_ids}"
    )


# =========================================================================
# Helpers
# =========================================================================


def _build_3x3_grid() -> tuple[dict[str, Node], dict[str, Edge]]:
    """Build a 3x3 grid road network.

    Topology:
      n1 -- n2 -- n3
      |     |     |
      n4 -- n5 -- n6
      |     |     |
      n7 -- n8 -- n9

    9 nodes, 12 bidirectional edges (24 directed records).
    Nodes are spaced 1.0 unit apart.
    """
    nodes: dict[str, Node] = {}
    coords = [
        ("n1", 0.0, 2.0),
        ("n2", 1.0, 2.0),
        ("n3", 2.0, 2.0),
        ("n4", 0.0, 1.0),
        ("n5", 1.0, 1.0),
        ("n6", 2.0, 1.0),
        ("n7", 0.0, 0.0),
        ("n8", 1.0, 0.0),
        ("n9", 2.0, 0.0),
    ]
    for nid, x, y in coords:
        nodes[nid] = Node(node_id=nid, position=Coord(x, y))

    edges: dict[str, Edge] = {}
    _edge_counter = itertools.count(1)

    def _add_bidirectional_edge(
        from_id: str,
        to_id: str,
        length_m: float = 100.0,
    ) -> None:
        """Add both directions for a two-way road segment."""
        n = next(_edge_counter)
        edges[f"e{n}a"] = Edge(
            edge_id=f"e{n}a",
            from_node=from_id,
            to_node=to_id,
            length_m=length_m,
        )
        n = next(_edge_counter)
        edges[f"e{n}b"] = Edge(
            edge_id=f"e{n}b",
            from_node=to_id,
            to_node=from_id,
            length_m=length_m,
        )

    # Horizontal edges (row 1-3)
    for row_start in ("n1", "n4", "n7"):
        n_a = row_start
        n_b = f"n{int(row_start[1]) + 1}"
        _add_bidirectional_edge(n_a, n_b)
        n_c = f"n{int(row_start[1]) + 2}"
        _add_bidirectional_edge(n_b, n_c)
    # Vertical edges (col 1-3)
    for col_offset in (0, 1, 2):
        top_id = f"n{1 + col_offset}"
        mid_id = f"n{4 + col_offset}"
        bot_id = f"n{7 + col_offset}"
        _add_bidirectional_edge(top_id, mid_id)
        _add_bidirectional_edge(mid_id, bot_id)

    return nodes, edges
