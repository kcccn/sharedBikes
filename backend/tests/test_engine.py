"""Tests for the simulation engine."""
import pytest
from app.core.engine import SimulationEngine, SimulationNotRunningError, SimState
from app.core.fleet import Bike, BikeState


@pytest.fixture
def engine() -> SimulationEngine:
    eng = SimulationEngine()
    eng.fleet.add_bike(Bike("b1"), "s1")
    eng.fleet.add_bike(Bike("b2"), "s1")
    eng.fleet.add_bike(Bike("b3"), "s2")
    eng.fleet._station_capacity.update({"s1": 30, "s2": 20})
    return eng


class TestSimulationEngine:
    def test_initial_state(self, engine: SimulationEngine) -> None:
        assert engine.state == SimState.STOPPED
        assert engine.tick == 0

    def test_start_transition(self, engine: SimulationEngine) -> None:
        engine.start()
        assert engine.state == SimState.RUNNING

    def test_start_is_idempotent(self, engine: SimulationEngine) -> None:
        engine.start()
        engine.start()
        assert engine.state == SimState.RUNNING

    def test_advance_requires_running(self, engine: SimulationEngine) -> None:
        with pytest.raises(SimulationNotRunningError):
            engine.advance()

    def test_advance_increments_tick(self, engine: SimulationEngine) -> None:
        engine.start()
        engine.advance(steps=5)
        assert engine.tick == 5

    def test_pause_halts_advance(self, engine: SimulationEngine) -> None:
        engine.start()
        engine.advance(steps=2)
        engine.pause()
        with pytest.raises(SimulationNotRunningError):
            engine.advance()

    def test_stop_resets_advance(self, engine: SimulationEngine) -> None:
        engine.start()
        engine.advance(steps=2)
        engine.stop()
        with pytest.raises(SimulationNotRunningError):
            engine.advance()

    def test_time_of_day(self, engine: SimulationEngine) -> None:
        engine.start()
        engine.advance(steps=60)
        assert engine.time_of_day() == "00:01"

    def test_snapshot_structure(self, engine: SimulationEngine) -> None:
        engine.start()
        snap = engine.advance(steps=1)
        assert snap.total_bikes == 3
        assert snap.docked_bikes == 3
