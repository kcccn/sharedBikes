"""Tests for city domain model."""

from __future__ import annotations

from app.core.city import City, LatLng, Station


def test_nearest_station(sample_city: City) -> None:
    near_s1 = LatLng(39.951, 116.352)  # very close to s1
    nearest = sample_city.find_nearest_station(near_s1)
    assert nearest is not None
    assert nearest.id == "s1"


def test_nearest_station_empty() -> None:
    empty = City(name="Empty", bounds=(LatLng(0, 0), LatLng(1, 1)))
    assert empty.find_nearest_station(LatLng(0.5, 0.5)) is None


def test_stations_in_zone(sample_city: City) -> None:
    stations = sample_city.stations_in_zone("z1")
    assert len(stations) == 2
    assert all(s.zone_id == "z1" for s in stations)


def test_stations_in_zone_nonexistent(sample_city: City) -> None:
    assert sample_city.stations_in_zone("z_missing") == []
