"""Tests for city domain model."""

import pytest

from app.core.city import City, LatLng, Node, Edge, Station, Zone


def _minimal_city() -> City:
    nodes = {
        "n1": Node(node_id="n1", position=LatLng(39.9, 116.4)),
        "n2": Node(node_id="n2", position=LatLng(39.9, 116.41)),
    }
    edges = {
        "e1": Edge(
            edge_id="e1", from_node="n1", to_node="n2",
            length_m=500.0, max_speed_kmh=30.0,
        ),
    }
    stations = {
        "s1": Station(station_id="s1", position=LatLng(39.9, 116.4), capacity=20, name="Station A"),
        "s2": Station(station_id="s2", position=LatLng(39.901, 116.41), capacity=30, name="Station B"),
    }
    zones = {
        "z1": Zone(zone_id="z1", name="Zone 1", polygon=[LatLng(39.9, 116.4), LatLng(39.91, 116.41)]),
    }
    return City(nodes=nodes, edges=edges, stations=stations, zones=zones)


class TestCity:
    def test_find_nearest_station_returns_closest(self):
        city = _minimal_city()
        station, dist = city.find_nearest_station(LatLng(39.9, 116.4))
        assert station is not None
        assert station.station_id == "s1"
        assert dist >= 0

    def test_find_nearest_station_empty_city(self):
        city = City(nodes={}, edges={}, stations={}, zones={})
        station, dist = city.find_nearest_station(LatLng(39.9, 116.4))
        assert station is None
        assert dist == float("inf")

    def test_travel_time_property(self):
        edge = Edge(edge_id="e1", from_node="n1", to_node="n2",
                    length_m=1000.0, max_speed_kmh=30.0)
        expected = (1.0 / 30.0) * 60  # 2 minutes
        assert edge.travel_time_min == pytest.approx(expected, rel=1e-6)

    def test_station_immutability(self):
        station = Station(station_id="s1", position=LatLng(39.9, 116.4), capacity=20)
        assert station.station_id == "s1"
        assert station.capacity == 20
        assert station.position.lat == 39.9
