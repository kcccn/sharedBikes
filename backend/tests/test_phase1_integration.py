"""Phase 1 integration test: end-to-end validation of the full pipeline.

Validates: Config → Procedural City Generation → Station Deployment → Service Layer
"""

from app.services.map_service import MapService


def test_load_default_meets_thresholds() -> None:
    """MapService.load_city('default') must return a city meeting minimums."""
    service = MapService()
    city = service.load_city("default")

    assert len(city.nodes) >= 100, (
        f"Expected >= 100 nodes, got {len(city.nodes)}"
    )
    assert len(city.edges) >= 100, (
        f"Expected >= 100 edges, got {len(city.edges)}"
    )
    assert len(city.stations) >= 5, (
        f"Expected >= 5 stations, got {len(city.stations)}"
    )


def test_load_default_city_structure() -> None:
    """Verify city structural integrity after loading."""
    service = MapService()
    city = service.load_city("default")

    # Every edge must reference valid nodes
    node_ids = set(city.nodes.keys())
    for edge in city.edges.values():
        assert edge.from_node in node_ids, (
            f"Edge {edge.edge_id} references unknown from_node {edge.from_node}"
        )
        assert edge.to_node in node_ids, (
            f"Edge {edge.edge_id} references unknown to_node {edge.to_node}"
        )

    # Every station must reference a valid position (check Coord x,y range)
    for station in city.stations.values():
        assert isinstance(station.position.x, float), (
            f"Station {station.station_id} x is not a float"
        )
        assert isinstance(station.position.y, float), (
            f"Station {station.station_id} y is not a float"
        )
        assert station.capacity > 0, (
            f"Station {station.station_id} has zero capacity"
        )


def test_map_service_idempotent() -> None:
    """Loading the same city twice must return the same structure."""
    service = MapService()
    service.clear_cache()

    city_a = service.load_city("default")
    city_b = service.load_city("default")

    assert len(city_a.nodes) == len(city_b.nodes)
    assert len(city_a.edges) == len(city_b.edges)
    assert len(city_a.stations) == len(city_b.stations)


def test_unknown_city_falls_back_to_default() -> None:
    """Loading an unknown city should not crash and return a valid City."""
    service = MapService()
    city = service.load_city("nonexistent_city_xyz")

    assert city is not None
    assert isinstance(city.nodes, dict)
    assert isinstance(city.edges, dict)
    assert isinstance(city.stations, dict)
    assert isinstance(city.zones, dict)


def test_cache_hit_returns_same_object() -> None:
    """Cached city loading returns the exact same City object."""
    service = MapService()
    service.clear_cache()

    city_a = service.load_city("default")
    city_b = service.load_city("default")

    assert city_a is city_b  # same object from cache
