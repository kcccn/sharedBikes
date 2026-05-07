"""Smoke tests for PR #65 new functionality."""

import sys
sys.path.insert(0, 'backend')

from app.services.demand_service import TripGenerator, DemandService, RuleBasedDemandService
from app.core.city import City, Station, LatLng, Node, Edge


def test_rule_based_demand_generates_trips():
    rds = RuleBasedDemandService()
    stations = {
        's1': Station('s1', LatLng(0, 0), 10, 'A'),
        's2': Station('s2', LatLng(1, 1), 10, 'B'),
        's3': Station('s3', LatLng(2, 2), 10, 'C'),
    }
    trips = rds.generate(480, stations)  # 8am = peak
    assert len(trips) > 0, "Should generate trips during peak hours"
    for t in trips:
        assert t.from_station in stations
        assert t.to_station in stations
        assert t.from_station != t.to_station, "Should skip self-loops"


def test_rule_based_demand_empty_stations():
    rds = RuleBasedDemandService()
    assert rds.generate(0, {}) == []


def test_demand_service_backward_compat():
    ds = DemandService()
    assert isinstance(ds, TripGenerator)
    assert ds.generate(0, {}) == []


def test_shortest_path_between_stations():
    nodes = {
        'n1': Node('n1', LatLng(0, 0)),
        'n2': Node('n2', LatLng(0.01, 0)),
        'n3': Node('n3', LatLng(0.02, 0.01)),
    }
    edges = {
        'e1': Edge('e1', 'n1', 'n2', 1100.0),
        'e2': Edge('e2', 'n2', 'n3', 1500.0),
    }
    stations = {
        'sA': Station('sA', LatLng(0.001, 0), 10),
        'sB': Station('sB', LatLng(0.019, 0.009), 10),
    }
    city = City(nodes=nodes, edges=edges, stations=stations, zones={})
    dist = city.shortest_path_distance('sA', 'sB')
    assert dist is not None
    assert dist > 0


def test_shortest_path_same_station():
    nodes = {'n1': Node('n1', LatLng(0, 0))}
    city = City(nodes=nodes, edges={}, stations={
        'sA': Station('sA', LatLng(0, 0), 10),
    }, zones={})
    assert city.shortest_path_distance('sA', 'sA') == 0.0


def test_shortest_path_unknown_station():
    city = City(nodes={}, edges={}, stations={
        'sA': Station('sA', LatLng(0, 0), 10),
    }, zones={})
    assert city.shortest_path_distance('sA', 'sX') is None


def test_tick_events_without_trip_generator():
    """Engine works without trip_generator (backward compat)."""
    from app.core.engine import SimulationEngine, SimState
    from app.core.fleet import Fleet
    from app.core.scheduler import GreedyThresholdStrategy
    from app.core.weather import Environment

    city = City(nodes={}, edges={}, stations={}, zones={})
    engine = SimulationEngine(
        city=city,
        fleet=Fleet(),
        environment=Environment(),
        strategy=GreedyThresholdStrategy(),
    )
    engine.start()
    snap = engine.advance(3)
    assert snap.total_bikes == 0
    assert engine.tick == 3
    assert len(engine.recent_events) == 3
    assert engine.recent_events[0].tick == 1


def test_tick_events_with_rule_based_generator():
    from app.core.engine import SimulationEngine, SimState
    from app.core.fleet import Fleet
    from app.core.scheduler import GreedyThresholdStrategy
    from app.core.weather import Environment

    city = City(nodes={}, edges={}, stations={
        's1': Station('s1', LatLng(0, 0), 10),
        's2': Station('s2', LatLng(1, 1), 10),
    }, zones={})
    fleet = Fleet()
    engine = SimulationEngine(
        city=city,
        fleet=fleet,
        environment=Environment(),
        strategy=GreedyThresholdStrategy(),
        trip_generator=RuleBasedDemandService(base_rate=1.0, peak_rate=1.0),
    )
    engine.start()
    events = engine._tick()
    assert events.tick == 1
    assert len(events.trips) > 0, "Should generate trips with rate=1.0"
    assert "s1" in events.station_inventory
    assert "s2" in events.station_inventory
