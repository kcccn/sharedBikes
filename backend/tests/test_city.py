"""Tests for the city model."""

import pytest

from app.core.city import City, LatLng, Node, Edge, Station, Zone


def test_nearest_station() -> None:
    center = LatLng(39.9042, 116.4074)  # Beijing center
    s1 = Station("s1", "East", LatLng(39.905, 116.408), 20)
    s2 = Station("s2", "West", LatLng(39.903, 116.406), 20)
    city = City("test", nodes=(), edges=(), stations=(s1, s2), zones=())
    nearest = city.nearest_station(center)
    assert nearest is not None
    assert nearest.station_id == "s1"


def test_find_station_not_found() -> None:
    city = City("test", nodes=(), edges=(), stations=(), zones=())
    assert city.find_station("nonexistent") is None
