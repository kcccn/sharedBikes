"""Tests for the city model."""
import pytest
from app.core.city import City, LatLng, Station, Node, Edge, Zone


@pytest.fixture
def sample_city() -> City:
    """A minimal city with 3 stations."""
    return City(
        name="Testville",
        nodes={
            "n1": Node("n1", LatLng(0.0, 0.0)),
            "n2": Node("n2", LatLng(1.0, 1.0)),
        },
        edges={
            "e1": Edge("e1", "n1", "n2", 1000.0),
        },
        stations={
            "s1": Station("s1", "Station A", LatLng(0.0, 0.0), 30, "z1"),
            "s2": Station("s2", "Station B", LatLng(0.01, 0.01), 20, "z1"),
            "s3": Station("s3", "Station C", LatLng(0.5, 0.5), 40, "z2"),
        },
        zones={
            "z1": Zone("z1", "Downtown"),
            "z2": Zone("z2", "Suburbs"),
        },
    )


class TestFindNearestStation:
    def test_exact_match(self, sample_city: City) -> None:
        result = sample_city.find_nearest_station(LatLng(0.0, 0.0))
        assert result is not None
        sid, dist = result
        assert sid == "s1"
        assert dist == pytest.approx(0.0, abs=1)

    def test_nearest_is_s2(self, sample_city: City) -> None:
        result = sample_city.find_nearest_station(LatLng(0.0105, 0.0105))
        assert result is not None
        assert result[0] == "s2"

    def test_stations_in_zone(self, sample_city: City) -> None:
        stations = sample_city.stations_in_zone("z1")
        assert len(stations) == 2
        assert {s.station_id for s in stations} == {"s1", "s2"}

    def test_total_capacity(self, sample_city: City) -> None:
        assert sample_city.total_capacity() == 90
