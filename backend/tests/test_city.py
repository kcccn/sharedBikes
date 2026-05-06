"""Tests for city domain model and spatial queries."""

from __future__ import annotations

import pytest

from app.core.city import City, LatLng, Station


@pytest.fixture
def sample_city() -> City:
    stations = {
        "s1": Station(id="s1", position=LatLng(0.0, 0.0), capacity=10),
        "s2": Station(id="s2", position=LatLng(0.001, 0.001), capacity=10),
        "s3": Station(id="s3", position=LatLng(0.01, 0.01), capacity=10),
    }
    return City(
        name="test",
        bounds=(LatLng(-1.0, -1.0), LatLng(1.0, 1.0)),
        stations=stations,
    )


class TestFindNearestStation:
    def test_empty_city_returns_none(self):
        city = City(name="empty", bounds=(LatLng(0, 0), LatLng(1, 1)))
        assert city.find_nearest_station(LatLng(0.5, 0.5)) is None

    def test_returns_closest_station(self, sample_city: City):
        near_s1 = LatLng(0.00001, 0.00001)
        nearest = sample_city.find_nearest_station(near_s1)
        assert nearest is not None
        assert nearest.id == "s1"

    def test_exact_position_match(self, sample_city: City):
        nearest = sample_city.find_nearest_station(LatLng(0.0, 0.0))
        assert nearest is not None
        assert nearest.id == "s1"


class TestStationsInZone:
    def test_empty_zone(self, sample_city: City):
        assert sample_city.stations_in_zone("nonexistent") == []

    def test_multi_station_zone(self):
        from app.core.city import Zone, ZoneType

        city = City(
            name="zones",
            bounds=(LatLng(0, 0), LatLng(1, 1)),
            stations={
                "s1": Station(id="s1", position=LatLng(0.0, 0.0), capacity=10, zone_id="z1"),
                "s2": Station(id="s2", position=LatLng(0.1, 0.1), capacity=10, zone_id="z1"),
                "s3": Station(id="s3", position=LatLng(0.5, 0.5), capacity=10),
            },
            zones={
                "z1": Zone(id="z1", name="Zone 1", zone_type=ZoneType.MIXED, center=LatLng(0.05, 0.05)),
            },
        )
        result = city.stations_in_zone("z1")
        assert len(result) == 2
        assert {s.id for s in result} == {"s1", "s2"}
