"""Tests for the simulation engine."""

import pytest

from app.core.city import City, LatLng
from app.core.engine import SimulationEngine, SimConfig, SimulationNotRunningError
from app.core.fleet import Bike, Fleet
from app.core.scheduler import GreedyThresholdStrategy


def _make_minimal_city() -> City:
    """A single-station city for engine testing."""
    return City(
        id="test",
        name="Test",
        nodes={},
        edges={},
        stations={
            "s1": type("Station", (), {"id": "s1", "name": "S1", "position": LatLng(0, 0),
                                       "capacity": 10, "altitude_m": 0.0})(),
        },
        zones={},
    )


def _make_fleet(count: int = 5) -> Fleet:
    bikes = {f"b{i}": Bike(bike_id=f"b{i}") for i in range(count)}
    fleet = Fleet(bikes)
    return fleet


@pytest.fixture
def engine():
    city = _make_minimal_city()
    fleet = _make_fleet()
    strategy = GreedyThresholdStrategy()
    cfg = SimConfig(ticks_per_day=1440, speed_multiplier=60, rebalance_interval_ticks=100)
    return SimulationEngine(city, fleet, strategy, config=cfg)


class TestEngineLifecycle:
    """Engine state transitions."""

    def test_initial_state_is_stopped(self, engine):
        assert engine.state.value == "stopped"

    def test_start_transitions_to_running(self, engine):
        engine.start()
        assert engine.state.value == "running"

    def test_advance_raises_when_stopped(self, engine):
        with pytest.raises(SimulationNotRunningError):
            engine.advance(1)

    def test_advance_returns_snapshot_after_tick(self, engine):
        engine.start()
        snap = engine.advance(1)
        assert snap.total_bikes == 5
        assert engine.tick == 1

    def test_pause_and_resume(self, engine):
        engine.start()
        engine.pause()
        assert engine.state.value == "paused"
        with pytest.raises(SimulationNotRunningError):
            engine.advance(1)

    def test_stop_resets_tick(self, engine):
        engine.start()
        engine.advance(10)
        engine.stop()
        assert engine.tick == 0
        assert engine.state.value == "stopped"
