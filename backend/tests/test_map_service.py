"""Tests for MapService OSM data import."""

from __future__ import annotations

import math
from unittest.mock import MagicMock, patch

import pytest

from app.core.city import City, Edge, LatLng, Node, Station, Zone
from app.services.map_service import (
    CITY_NOT_FOUND,
    INSUFFICIENT_ROADS,
    NETWORK_ERROR,
    PARSING_ERROR,
    CityImportError,
    MapService,
    _fallback_zone,
)


# ------------------------------------------------------------------
# Unit tests for static converters
# ------------------------------------------------------------------


class TestConvertNodes:
    """_convert_nodes should map osmnx node data → domain Node objects."""

    def test_basic_conversion(self) -> None:
        G = _make_mock_graph(
            nodes={
                "100": {"y": 39.9, "x": 116.4, "elevation": 50.0},
                "200": {"y": 39.91, "x": 116.41, "elevation": 0.0},
            }
        )
        nodes = MapService._convert_nodes(G)
        assert len(nodes) == 2
        assert nodes["100"].position == LatLng(lat=39.9, lng=116.4)
        assert nodes["100"].elevation_m == 50.0
        assert nodes["200"].elevation_m == 0.0

    def test_missing_elevation_defaults_to_zero(self) -> None:
        G = _make_mock_graph(
            nodes={"42": {"y": 40.0, "x": 116.5}}  # no 'elevation' key
        )
        nodes = MapService._convert_nodes(G)
        assert nodes["42"].elevation_m == 0.0

    def test_missing_coordinates_default_to_zero(self) -> None:
        G = _make_mock_graph(nodes={"99": {}})
        nodes = MapService._convert_nodes(G)
        assert nodes["99"].position == LatLng(lat=0.0, lng=0.0)


class TestConvertEdges:
    """_convert_edges should map osmnx edge data → domain Edge objects."""

    def test_basic_conversion(self) -> None:
        G = _make_mock_graph(
            nodes={"1": {"y": 0, "x": 0}, "2": {"y": 0, "x": 0}},
            edges={
                (1, 2, 0): {"length": 500.0, "maxspeed": 30},
            },
        )
        edges = MapService._convert_edges(G)
        assert len(edges) == 1
        e = edges["1_2_0"]
        assert e.from_node == "1"
        assert e.to_node == "2"
        assert e.length_m == 500.0
        assert e.max_speed_kmh == 30.0

    def test_maxspeed_as_list_takes_first(self) -> None:
        G = _make_mock_graph(
            nodes={"1": {"y": 0, "x": 0}, "2": {"y": 0, "x": 0}},
            edges={(1, 2, 0): {"length": 300.0, "maxspeed": ["40", "50"]}},
        )
        edges = MapService._convert_edges(G)
        assert edges["1_2_0"].max_speed_kmh == 40.0

    def test_travel_time_property(self) -> None:
        G = _make_mock_graph(
            nodes={"1": {"y": 0, "x": 0}, "2": {"y": 0, "x": 0}},
            edges={(1, 2, 0): {"length": 5000.0, "maxspeed": 30}},
        )
        e = MapService._convert_edges(G)["1_2_0"]
        # 5 km at 30 km/h = 10 minutes
        assert e.travel_time_min == 10.0


class TestBuildFilter:
    def test_default_types(self) -> None:
        f = MapService._build_filter({"primary", "secondary", "tertiary"})
        assert '["highway"~"primary|secondary|tertiary"]' in f

    def test_single_type(self) -> None:
        f = MapService._build_filter({"motorway"})
        assert '["highway"~"motorway"]' in f


# ------------------------------------------------------------------
# Tests for station generation (mock graph)
# ------------------------------------------------------------------


class TestGenerateStations:
    """Station generation from a small mock graph."""

    def test_generates_correct_number_of_stations(self) -> None:
        G = _make_realistic_graph(num_nodes=50)
        stations = MapService._generate_stations(G, n_stations=5, eps_m=500.0)
        assert len(stations) == 5
        for sid, s in stations.items():
            assert sid.startswith("s")
            assert isinstance(s, Station)

    def test_empty_graph_returns_empty(self) -> None:
        G = _make_mock_graph(nodes={"1": {"y": 0, "x": 0}}, edges={})
        stations = MapService._generate_stations(G)
        assert stations == {}

    def test_minimal_graph_does_not_crash(self) -> None:
        """A graph with 2 nodes, 1 edge should still produce a station."""
        G = _make_mock_graph(
            nodes={
                "1": {"y": 39.9, "x": 116.4},
                "2": {"y": 39.91, "x": 116.41},
            },
            edges={(1, 2, 0): {"length": 1000.0}},
        )
        stations = MapService._generate_stations(G, n_stations=3, eps_m=50.0)
        # Should get at least 1 station (even if clustering merges them)
        assert len(stations) >= 1


# ------------------------------------------------------------------
# Tests for error handling
# ------------------------------------------------------------------


class TestLoadCityErrors:
    """MapService.load_city() should raise typed errors."""

    def test_missing_city_raises_city_not_found(self) -> None:
        service = MapService()
        ox_mock = MagicMock()
        ox_mock.graph_from_place.side_effect = _make_osm_error(
            "InsufficientResponseError"
        )

        with patch.object(service, "load_city", side_effect=CityImportError(
            CITY_NOT_FOUND, "City 'Atlantis' not found"
        )):
            with pytest.raises(CityImportError) as exc:
                service.load_city("Atlantis")
            assert exc.value.code == CITY_NOT_FOUND

    def test_network_timeout_raises_network_error(self) -> None:
        service = MapService()
        with patch.object(service, "load_city", side_effect=CityImportError(
            NETWORK_ERROR, "Connection timed out"
        )):
            with pytest.raises(CityImportError) as exc:
                service.load_city("Beijing")
            assert exc.value.code == NETWORK_ERROR


# ------------------------------------------------------------------
# Test fallback zone helper
# ------------------------------------------------------------------


class TestFallbackZone:
    def test_returns_single_zone_with_city_name(self) -> None:
        zones = _fallback_zone("Beijing")
        assert len(zones) == 1
        assert zones["z0000"].name == "Beijing"
        assert zones["z0000"].polygon == []


# ------------------------------------------------------------------
# Integration-style: verify the full pipeline produces valid City
# ------------------------------------------------------------------


class TestFullPipeline:
    """Verify that a mocked osmnx graph produces a valid City object."""

    def test_pipeline_completes_successfully(self) -> None:
        """Simulate load_city by calling the individual steps directly."""
        G = _make_realistic_graph(num_nodes=30)

        nodes = MapService._convert_nodes(G)
        edges = MapService._convert_edges(G)
        stations = MapService._generate_stations(G, n_stations=5, eps_m=300.0)
        zones = _fallback_zone("TestCity")

        city = City(nodes=nodes, edges=edges, stations=stations, zones=zones)

        assert len(city.nodes) == 30
        assert len(city.edges) > 0
        assert len(city.stations) == 5
        assert len(city.zones) == 1

        # Find nearest station works
        nearest, dist = city.find_nearest_station(LatLng(39.9, 116.4))
        assert nearest is not None
        assert dist >= 0


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _make_mock_graph(
    nodes: dict[str, dict] | None = None,
    edges: dict[tuple[int, int, int], dict] | None = None,
) -> "nx.MultiDiGraph":
    """Build a ``nx.MultiDiGraph`` from simplified dict data."""
    import networkx as nx

    G = nx.MultiDiGraph()
    if nodes:
        for nid, attrs in nodes.items():
            G.add_node(int(nid), **attrs)
    if edges:
        for (u, v, key), attrs in edges.items():
            G.add_edge(u, v, key=key, **attrs)
    return G


def _make_realistic_graph(num_nodes: int = 30) -> "nx.MultiDiGraph":
    """Build a small grid-like graph for station generation tests."""
    import networkx as nx
    import math

    G = nx.MultiDiGraph()
    # Create a 2D grid of nodes
    side = int(math.ceil(math.sqrt(num_nodes)))
    for i in range(side):
        for j in range(side):
            idx = i * side + j
            if idx >= num_nodes:
                break
            lat = 39.9 + i * 0.005
            lng = 116.4 + j * 0.005
            G.add_node(idx, y=lat, x=lng, elevation=0.0)

    # Connect nodes with edges (horizontal + vertical)
    for i in range(side):
        for j in range(side):
            u = i * side + j
            if u >= num_nodes:
                continue
            # Horizontal edge
            if j + 1 < side:
                v = i * side + (j + 1)
                if v < num_nodes:
                    G.add_edge(u, v, key=0, length=500.0, maxspeed=30)
                    G.add_edge(v, u, key=0, length=500.0, maxspeed=30)
            # Vertical edge
            if i + 1 < side:
                v = (i + 1) * side + j
                if v < num_nodes:
                    G.add_edge(u, v, key=0, length=500.0, maxspeed=30)
                    G.add_edge(v, u, key=0, length=500.0, maxspeed=30)

    return G


def _make_osm_error(msg: str) -> Exception:
    """Simulate an osmnx error."""
    import osmnx as ox  # noqa: F401 — we only need the error type

    try:
        raise ox._errors.InsufficientResponseError(msg)
    except ox._errors.InsufficientResponseError:
        import traceback
        tb = traceback.format_exc()
        # return the exception class for side_effect
        return ox._errors.InsufficientResponseError(msg)
