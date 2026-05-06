"""Phase 1 integration test: end-to-end validation of the full pipeline.

Validates: Config → Map Parsing → Station Deployment → Service Layer
"""

import time

from app.services.map_service import MapService


def test_load_beijing_meets_thresholds() -> None:
    """MapService.load_city('beijing') must return a city meeting Phase 1 minimums."""
    service = MapService()
    city = service.load_city("beijing")

    assert len(city.nodes) >= 1000, (
        f"Expected >= 1000 nodes, got {len(city.nodes)}"
    )
    assert len(city.edges) >= 2000, (
        f"Expected >= 2000 edges, got {len(city.edges)}"
    )
    assert len(city.stations) >= 200, (
        f"Expected >= 200 stations, got {len(city.stations)}"
    )


def test_load_beijing_city_structure() -> None:
    """Verify city structural integrity after loading."""
    service = MapService()
    city = service.load_city("beijing")

    # Every edge must reference valid nodes
    node_ids = set(city.nodes.keys())
    for edge in city.edges.values():
        assert edge.from_node in node_ids, (
            f"Edge {edge.edge_id} references unknown from_node {edge.from_node}"
        )
        assert edge.to_node in node_ids, (
            f"Edge {edge.edge_id} references unknown to_node {edge.to_node}"
        )

    # Every station must reference a valid position (check lat/lng range)
    for station in city.stations.values():
        assert 39.5 <= station.position.lat <= 40.2, (
            f"Station {station.station_id} lat {station.position.lat} out of Beijing range"
        )
        assert 116.0 <= station.position.lng <= 116.8, (
            f"Station {station.station_id} lng {station.position.lng} out of Beijing range"
        )
        assert station.capacity > 0, (
            f"Station {station.station_id} has zero capacity"
        )

    # Zones should be present
    assert len(city.zones) > 0, "City should have at least one operational zone"


def test_cache_hit_performance() -> None:
    """Cached city loading must be fast (< 2s)."""
    service = MapService()
    service.clear_cache()

    # First load (cold cache) — allow up to 30s
    t0 = time.perf_counter()
    service.load_city("beijing")
    cold_load_time = time.perf_counter() - t0

    # Second load (warm cache) — must be < 2s
    t0 = time.perf_counter()
    service.load_city("beijing")
    cache_load_time = time.perf_counter() - t0

    assert cold_load_time < 30.0, (
        f"Cold load took {cold_load_time:.2f}s (limit 30s)"
    )
    assert cache_load_time < 2.0, (
        f"Cache load took {cache_load_time:.2f}s (limit 2s)"
    )


def test_map_service_idempotent() -> None:
    """Loading the same city twice must return the same structure."""
    service = MapService()
    service.clear_cache()

    city_a = service.load_city("beijing")
    city_b = service.load_city("beijing")

    assert len(city_a.nodes) == len(city_b.nodes)
    assert len(city_a.edges) == len(city_b.edges)
    assert len(city_a.stations) == len(city_b.stations)
    # Verify first node is identical
    first_nid = next(iter(city_a.nodes))
    assert city_a.nodes[first_nid] == city_b.nodes[first_nid]


def test_unknown_city_returns_minimal() -> None:
    """Loading an unknown city name should not crash and return a valid City."""
    service = MapService()
    city = service.load_city("nonexistent_city_xyz")

    assert city is not None
    assert isinstance(city.nodes, dict)
    assert isinstance(city.edges, dict)
    assert isinstance(city.stations, dict)
    assert isinstance(city.zones, dict)
