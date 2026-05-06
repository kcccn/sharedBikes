"""Tests for city domain model."""

from app.core.city import City, LatLng, Node, Edge, Station, Zone


def test_empty_city() -> None:
    city = City(nodes={}, edges={}, stations={}, zones={})
    assert len(city.nodes) == 0
    assert len(city.edges) == 0
    assert len(city.stations) == 0
    assert len(city.zones) == 0


def test_find_nearest_station_empty() -> None:
    city = City(nodes={}, edges={}, stations={}, zones={})
    station, dist = city.find_nearest_station(LatLng(lat=0.0, lng=0.0))
    assert station is None
    assert dist == float("inf")


def test_find_nearest_station() -> None:
    s1 = Station(station_id="s1", position=LatLng(lat=39.9, lng=116.4), capacity=20)
    s2 = Station(station_id="s2", position=LatLng(lat=39.91, lng=116.41), capacity=30)
    city = City(
        nodes={},
        edges={},
        stations={"s1": s1, "s2": s2},
        zones={},
    )
    station, dist = city.find_nearest_station(LatLng(lat=39.9, lng=116.4))
    assert station is not None
    assert station.station_id == "s1"
    assert dist >= 0


def test_edge_travel_time() -> None:
    edge = Edge(edge_id="e1", from_node="n1", to_node="n2", length_m=1000, max_speed_kmh=30)
    assert edge.travel_time_min == 2.0  # 1 km at 30 km/h = 2 min
