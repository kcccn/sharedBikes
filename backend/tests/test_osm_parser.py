"""Tests for the OSM parser — all tests use synthetic graphs to avoid network calls."""

from __future__ import annotations

import math

import networkx as nx
import pytest

from app.core.city import City, Edge, LatLng, Node
from app.services.osm_parser import (
    OSMError,
    _graph_to_city,
    _highway_allowed,
    _parse_maxspeed,
    _parse_single_maxspeed,
)


# ======================================================================
# _graph_to_city — the core conversion
# ======================================================================


def _make_graph(
    *,
    with_coords: bool = True,
    highway: str = "primary",
    length: float = 100.0,
    maxspeed: str | None = "50",
) -> nx.MultiDiGraph:
    """Build a minimal osmnx-style MultiDiGraph for testing."""
    G = nx.MultiDiGraph()
    G.add_node(1, y=39.9 if with_coords else None, x=116.4 if with_coords else None)
    G.add_node(2, y=39.91 if with_coords else None, x=116.41 if with_coords else None)
    attrs: dict = {"highway": highway, "length": length}
    if maxspeed is not None:
        attrs["maxspeed"] = maxspeed
    G.add_edge(1, 2, 0, **attrs)
    return G


class TestGraphToCity:
    def test_basic_conversion(self) -> None:
        G = _make_graph()
        city = _graph_to_city(G)

        assert len(city.nodes) == 2
        assert len(city.edges) == 1
        assert city.stations == {}
        assert city.zones == {}

        # Node checks
        n1 = city.nodes["1"]
        assert n1.node_id == "1"
        assert n1.position.lat == 39.9
        assert n1.position.lng == 116.4
        assert n1.elevation_m == 0.0

        # Edge checks
        e1 = list(city.edges.values())[0]
        assert e1.from_node == "1"
        assert e1.to_node == "2"
        assert e1.length_m == 100.0
        assert e1.max_speed_kmh == 50.0

    def test_skips_nodes_without_coordinates(self) -> None:
        G = _make_graph(with_coords=False)
        with pytest.raises(OSSMError, match="no valid nodes"):
            _graph_to_city(G)

    def test_skips_edges_with_missing_endpoints(self) -> None:
        G = nx.MultiDiGraph()
        G.add_node(1, y=39.9, x=116.4)  # only node 1 has coords
        G.add_node(2, y=None, x=None)  # node 2 will be skipped
        G.add_edge(1, 2, 0, highway="primary", length=100.0)

        with pytest.raises(OSSMError, match="no valid edges"):
            _graph_to_city(G)

    def test_filters_disallowed_highway(self) -> None:
        G = _make_graph(highway="motorway")
        with pytest.raises(OSSMError, match="no valid edges"):
            _graph_to_city(G)

    def test_accepts_list_highway_with_one_allowed(self) -> None:
        G = _make_graph()
        # Override highway to be a list with one allowed type
        u, v, k, data = next(iter(G.edges(keys=True, data=True)))
        data["highway"] = ["primary", "trunk"]

        city = _graph_to_city(G)
        assert len(city.edges) == 1

    def test_rejects_list_highway_with_none_allowed(self) -> None:
        G = _make_graph()
        u, v, k, data = next(iter(G.edges(keys=True, data=True)))
        data["highway"] = ["motorway", "trunk"]

        with pytest.raises(OSSMError, match="no valid edges"):
            _graph_to_city(G)

    def test_handles_missing_maxspeed_defaults_to_30(self) -> None:
        G = _make_graph(maxspeed=None)
        city = _graph_to_city(G)
        edge = next(iter(city.edges.values()))
        assert edge.max_speed_kmh == 30.0

    def test_handles_maxspeed_list(self) -> None:
        G = _make_graph()
        u, v, k, data = next(iter(G.edges(keys=True, data=True)))
        data["maxspeed"] = ["60", "80"]

        city = _graph_to_city(G)
        edge = next(iter(city.edges.values()))
        # Takes minimum
        assert edge.max_speed_kmh == 60.0

    def test_preserves_elevation(self) -> None:
        G = nx.MultiDiGraph()
        G.add_node(1, y=39.9, x=116.4, elevation=50.0)
        G.add_node(2, y=39.91, x=116.41, elevation=100.0)
        G.add_edge(1, 2, 0, highway="primary", length=200.0, maxspeed="40")

        city = _graph_to_city(G)
        assert city.nodes["1"].elevation_m == 50.0
        assert city.nodes["2"].elevation_m == 100.0

    def test_multiple_edges_same_nodes_different_keys(self) -> None:
        G = nx.MultiDiGraph()
        G.add_node(1, y=39.9, x=116.4)
        G.add_node(2, y=39.91, x=116.41)
        G.add_edge(1, 2, 0, highway="primary", length=100.0, maxspeed="50")
        G.add_edge(1, 2, 1, highway="secondary", length=150.0, maxspeed="40")

        city = _graph_to_city(G)
        assert len(city.edges) == 2

    def test_empty_graph_raises(self) -> None:
        G = nx.MultiDiGraph()
        with pytest.raises(OSSMError, match="no valid nodes"):
            _graph_to_city(G)

    def test_invalid_bbox_raises(self) -> None:
        from app.services.osm_parser import parse_from_bbox

        with pytest.raises(OSSMError, match="Invalid bounding box"):
            parse_from_bbox(north=30, south=40, east=120, west=110)

    def test_nonexistent_file_raises(self) -> None:
        from app.services.osm_parser import parse_from_file

        with pytest.raises(OSSMError, match="OSM file not found"):
            parse_from_file("/nonexistent/file.osm.pbf")


# ======================================================================
# _highway_allowed
# ======================================================================


class TestHighwayAllowed:
    def test_allows_primary(self) -> None:
        assert _highway_allowed("primary")

    def test_allows_secondary(self) -> None:
        assert _highway_allowed("secondary")

    def test_allows_tertiary(self) -> None:
        assert _highway_allowed("tertiary")

    def test_allows_residential(self) -> None:
        assert _highway_allowed("residential")

    def test_rejects_motorway(self) -> None:
        assert not _highway_allowed("motorway")

    def test_rejects_none(self) -> None:
        assert not _highway_allowed(None)

    def test_rejects_empty_string(self) -> None:
        assert not _highway_allowed("")

    def test_list_with_allowed(self) -> None:
        assert _highway_allowed(["primary", "trunk"])

    def test_list_without_allowed(self) -> None:
        assert not _highway_allowed(["motorway", "trunk"])

    def test_empty_list(self) -> None:
        assert not _highway_allowed([])


# ======================================================================
# _parse_maxspeed / _parse_single_maxspeed
# ======================================================================


class TestParseMaxspeed:
    def test_none_returns_default(self) -> None:
        assert _parse_maxspeed(None) == 30.0

    def test_numeric_string(self) -> None:
        assert _parse_maxspeed("50") == 50.0

    def test_with_kmh_unit(self) -> None:
        assert _parse_maxspeed("50 km/h") == 50.0

    def test_with_kph_unit(self) -> None:
        assert _parse_maxspeed("60 kph") == 60.0

    def test_with_mph_converts(self) -> None:
        result = _parse_maxspeed("30 mph")
        assert abs(result - 48.3) < 0.1  # 30 * 1.609344 ≈ 48.28

    def test_list_takes_minimum(self) -> None:
        assert _parse_maxspeed(["50", "80"]) == 50.0

    def test_list_with_mph(self) -> None:
        result = _parse_maxspeed(["30 mph", "50"])
        assert abs(result - 48.3) < 0.1

    def test_float_input(self) -> None:
        assert _parse_maxspeed(55.5) == 55.5

    def test_gibberish_falls_back(self) -> None:
        assert _parse_maxspeed("fast") == 30.0

    def test_decimal_number(self) -> None:
        assert _parse_maxspeed("55.5") == 55.5
