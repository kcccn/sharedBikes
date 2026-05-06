"""Tests for the city model."""

from app.core.city import City, LatLng, Node, Edge, Station, Zone


def _make_demo_city() -> City:
    """Build a minimal 2-node, 1-edge, 2-station city for testing."""
    nodes = {
        "n1": Node(id="n1", position=LatLng(39.9, 116.4)),
        "n2": Node(id="n2", position=LatLng(39.91, 116.41)),
    }
    edges = {
        "e1": Edge(id="e1", from_node="n1", to_node="n2", length_m=1200.0),
    }
    stations = {
        "s1": Station(id="s1", name="Station A", position=LatLng(39.9, 116.4), capacity=30),
        "s2": Station(id="s2", name="Station B", position=LatLng(39.905, 116.405), capacity=20),
    }
    zones = {
        "z1": Zone(
            id="z1",
            name="Downtown",
            polygon=(
                LatLng(39.89, 116.38),
                LatLng(39.91, 116.38),
                LatLng(39.91, 116.42),
                LatLng(39.89, 116.42),
            ),
        ),
    }
    return City(id="demo", name="Demo City", nodes=nodes, edges=edges, stations=stations, zones=zones)


class TestCity:
    """City model unit tests."""

    def setup_method(self) -> None:
        self.city = _make_demo_city()

    def test_find_nearest_station_returns_nearest(self) -> None:
        """Nearest station to n1 should be s1 (same position)."""
        nearest = self.city.find_nearest_station(LatLng(39.9, 116.4))
        assert nearest is not None
        assert nearest.id == "s1"

    def test_find_nearest_station_returns_none_for_empty_city(self) -> None:
        """A city with no stations should return None."""
        empty = City(id="empty", name="Empty", nodes={}, edges={}, stations={}, zones={})
        assert empty.find_nearest_station(LatLng(0, 0)) is None

    def test_station_has_expected_attributes(self) -> None:
        s = self.city.stations["s2"]
        assert s.name == "Station B"
        assert s.capacity == 20

    def test_node_is_frozen(self) -> None:
        n = Node(id="test", position=LatLng(1, 2))
        assert n.id == "test"
        # NamedTuple is immutable
        assert isinstance(n.position, LatLng)
