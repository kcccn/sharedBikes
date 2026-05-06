"""Tests for city domain models."""
import math

from app.core.city import City, LatLng, Node, Edge, Station, Zone


def test_find_nearest_station_returns_closest() -> None:
    center = LatLng(39.9, 116.4)
    nodes = {"n1": Node(node_id="n1", position=center)}
    stations = {
        "s1": Station(station_id="s1", name="A", position=LatLng(39.91, 116.41), capacity=20),
        "s2": Station(station_id="s2", name="B", position=LatLng(39.92, 116.42), capacity=30),
    }
    zones = {}
    city = City(nodes=nodes, edges={}, stations=stations, zones=zones)

    nearest, dist = city.find_nearest_station(LatLng(39.905, 116.405))
    assert nearest is not None
    assert nearest.station_id == "s1"  # s1 is closer


def test_find_nearest_station_empty_returns_none() -> None:
    city = City(nodes={}, edges={}, stations={}, zones={})
    nearest, dist = city.find_nearest_station(LatLng(39.9, 116.4))
    assert nearest is None
    assert dist == math.inf


def test_edge_travel_time() -> None:
    edge = Edge(edge_id="e1", from_node="n1", to_node="n2", length_m=5000, max_speed_kmh=30)
    # 5 km at 30 km/h = 10 minutes
    assert edge.travel_time_min == 10.0
