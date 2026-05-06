"""Tests for Station auto-generation algorithm."""

from app.core.city import Edge, LatLng, Node
from app.core.station_generator import generate_stations


def _make_node(nid: str, lat: float, lng: float) -> Node:
    return Node(node_id=nid, position=LatLng(lat, lng))


def _make_edge(eid: str, frm: str, to: str, length: float = 100) -> Edge:
    return Edge(edge_id=eid, from_node=frm, to_node=to, length_m=length)


def test_empty_nodes_returns_empty() -> None:
    assert generate_stations({}, {}) == {}


def test_single_node_creates_one_station() -> None:
    nodes = {"n1": _make_node("n1", 39.9, 116.4)}
    stations = generate_stations(nodes, {})
    assert len(stations) == 1
    s = stations["station-auto-n1"]
    assert s.position == LatLng(39.9, 116.4)


def test_two_close_nodes_deduplicated() -> None:
    """Nodes within min_distance_km should not both get stations."""
    nodes = {
        "n1": _make_node("n1", 39.9, 116.4),
        "n2": _make_node("n2", 39.901, 116.401),  # ~0.13 km away
    }
    stations = generate_stations(nodes, {}, min_distance_km=0.3)
    assert len(stations) == 1  # n2 is too close


def test_two_far_nodes_both_get_stations() -> None:
    nodes = {
        "n1": _make_node("n1", 39.9, 116.4),
        "n2": _make_node("n2", 39.95, 116.45),  # ~7 km away
    }
    stations = generate_stations(nodes, {}, min_distance_km=0.3)
    assert len(stations) == 2


def test_degree_based_prioritisation() -> None:
    """Nodes with higher degree (more edges) should be placed first."""
    nodes = {
        "n1": _make_node("n1", 39.90, 116.40),
        "n2": _make_node("n2", 39.92, 116.42),  # far enough from n1
    }
    edges = {
        "e1": _make_edge("e1", "n1", "n2", 500),
    }
    stations = generate_stations(nodes, edges, min_distance_km=0.3)
    # Both nodes have degree 1, so both should be placed
    assert len(stations) == 2
    assert "station-auto-n1" in stations
    assert "station-auto-n2" in stations


def test_capacity_scales_with_degree() -> None:
    """Higher degree nodes get larger capacity."""
    nodes = {
        "n1": _make_node("n1", 39.90, 116.40),
        "n2": _make_node("n2", 39.92, 116.42),
        "n3": _make_node("n3", 39.94, 116.44),
    }
    # n1 has degree 3 (connected to both), n2 and n3 have degree 1
    edges = {
        "e1": _make_edge("e1", "n1", "n2", 300),
        "e2": _make_edge("e2", "n1", "n3", 300),
        "e3": _make_edge("e3", "n2", "n3", 300),
    }
    stations = generate_stations(nodes, edges, min_distance_km=0.3)
    # All are placed since far enough apart
    assert "station-auto-n1" in stations
    assert stations["station-auto-n1"].capacity >= stations["station-auto-n2"].capacity


def test_max_stations_limit() -> None:
    nodes = {
        f"n{i}": _make_node(f"n{i}", 39.9 + i * 0.05, 116.4 + i * 0.05)
        for i in range(20)
    }
    stations = generate_stations(nodes, {}, min_distance_km=0.01, max_stations=5)
    assert len(stations) <= 5


def test_fallback_no_edges() -> None:
    """When no edges exist, use grid fallback."""
    nodes = {
        "n1": _make_node("n1", 39.9, 116.4),
        "n2": _make_node("n2", 39.95, 116.45),
    }
    stations = generate_stations(nodes, {})
    assert len(stations) == 2
