"""Tests for simulation engine."""

import pytest

from app.core.city import City, LatLng
from app.core.engine import SimulationEngine, SimState, SimulationNotRunningError
from app.core.fleet import Fleet, Bike, BikeStatus
from app.core.scheduler import GreedyThresholdStrategy
from app.core.weather import Environment


def _empty_city() -> City:
    return City(nodes={}, edges={}, stations={}, zones={})


class TestSimulationEngine:
    def test_initial_state_is_stopped(self):
        engine = SimulationEngine(
            city=_empty_city(),
            fleet=Fleet(),
            environment=Environment(),
            strategy=GreedyThresholdStrategy(),
        )
        assert engine.state == SimState.STOPPED

    def test_start_transitions_to_running(self):
        engine = SimulationEngine(
            city=_empty_city(),
            fleet=Fleet(),
            environment=Environment(),
            strategy=GreedyThresholdStrategy(),
        )
        engine.start()
        assert engine.state == SimState.RUNNING

    def test_advance_raises_when_stopped(self):
        engine = SimulationEngine(
            city=_empty_city(),
            fleet=Fleet(),
            environment=Environment(),
            strategy=GreedyThresholdStrategy(),
        )
        with pytest.raises(SimulationNotRunningError):
            engine.advance(1)

    def test_advance_increments_tick(self):
        engine = SimulationEngine(
            city=_empty_city(),
            fleet=Fleet(),
            environment=Environment(),
            strategy=GreedyThresholdStrategy(),
        )
        engine.start()
        snapshot = engine.advance(5)
        assert engine.tick == 5
        assert snapshot is not None

    def test_pause_raises_when_stopped(self):
        engine = SimulationEngine(
            city=_empty_city(),
            fleet=Fleet(),
            environment=Environment(),
            strategy=GreedyThresholdStrategy(),
        )
        with pytest.raises(SimulationNotRunningError):
            engine.pause()

    def test_stop_resets_state(self):
        engine = SimulationEngine(
            city=_empty_city(),
            fleet=Fleet(),
            environment=Environment(),
            strategy=GreedyThresholdStrategy(),
        )
        engine.start()
        engine.advance(10)
        engine.stop()
        assert engine.state == SimState.STOPPED
        assert engine.tick == 0

    def test_time_of_day_format(self):
        engine = SimulationEngine(
            city=_empty_city(),
            fleet=Fleet(),
            environment=Environment(),
            strategy=GreedyThresholdStrategy(),
        )
        engine.start()
        # After 0 ticks → 00:00
        assert engine.time_of_day() == "00:00"
