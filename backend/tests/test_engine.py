"""Tests for the simulation engine lifecycle and tick mechanics."""

from __future__ import annotations

import pytest

from app.core.city import City, LatLng
from app.core.engine import (
    SimulationEngine,
    SimulationNotRunningError,
    SimState,
)
from app.core.fleet import Bike, BikeStatus, Fleet


@pytest.fixture
def engine() -> SimulationEngine:
    city = City(name="test", bounds=(LatLng(0, 0), LatLng(1, 1)))
    return SimulationEngine(city=city)


class TestLifecycle:
    def test_initial_state(self, engine: SimulationEngine):
        assert engine.state == SimState.STOPPED
        assert engine.tick == 0

    def test_start_changes_state(self, engine: SimulationEngine):
        engine.start()
        assert engine.state == SimState.RUNNING

    def test_start_twice_raises(self, engine: SimulationEngine):
        engine.start()
        with pytest.raises(RuntimeError, match="already running"):
            engine.start()

    def test_pause(self, engine: SimulationEngine):
        engine.start()
        engine.pause()
        assert engine.state == SimState.PAUSED

    def test_pause_when_stopped_raises(self, engine: SimulationEngine):
        with pytest.raises(RuntimeError, match="Can only pause a running simulation"):
            engine.pause()

    def test_stop(self, engine: SimulationEngine):
        engine.start()
        engine.stop()
        assert engine.state == SimState.STOPPED


class TestAdvance:
    def test_advance_while_stopped_raises(self, engine: SimulationEngine):
        with pytest.raises(SimulationNotRunningError):
            engine.advance()

    def test_advance_increments_tick(self, engine: SimulationEngine):
        engine.start()
        engine.advance()
        assert engine.tick == 1

    def test_advance_multiple_steps(self, engine: SimulationEngine):
        engine.start()
        engine.advance(steps=10)
        assert engine.tick == 10

    def test_advance_returns_snapshot(self, engine: SimulationEngine):
        engine.start()
        snapshot = engine.advance()
        assert snapshot.total_bikes == 0


class TestTimeOfDay:
    def test_midnight(self, engine: SimulationEngine):
        engine.tick = 0
        assert engine.time_of_day() == "00:00"

    def test_noon(self, engine: SimulationEngine):
        engine.tick = 720  # 12 hours * 60 min
        assert engine.time_of_day() == "12:00"

    def test_wraps_around_midnight(self, engine: SimulationEngine):
        engine.tick = 1440  # full day, back to 00:00
        assert engine.time_of_day() == "00:00"

    def test_day_number(self, engine: SimulationEngine):
        engine.tick = 0
        assert engine.day_number() == 1
        engine.tick = 1440
        assert engine.day_number() == 2
        engine.tick = 2880
        assert engine.day_number() == 3
