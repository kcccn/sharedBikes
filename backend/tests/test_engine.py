"""Tests for simulation engine."""

import pytest

from app.core.city import City, LatLng
from app.core.engine import SimulationEngine, SimulationNotRunningError, SimState
from app.core.fleet import Fleet
from app.core.scheduler import GreedyThresholdStrategy
from app.core.weather import Environment


@pytest.fixture
def engine() -> SimulationEngine:
    city = City(nodes={}, edges={}, stations={}, zones={})
    fleet = Fleet()
    env = Environment()
    strategy = GreedyThresholdStrategy()
    return SimulationEngine(
        city=city,
        fleet=fleet,
        environment=env,
        strategy=strategy,
    )


def test_initial_state(engine: SimulationEngine) -> None:
    assert engine.state == SimState.STOPPED
    assert engine.tick == 0


def test_start(engine: SimulationEngine) -> None:
    engine.start()
    assert engine.state == SimState.RUNNING


def test_pause_running(engine: SimulationEngine) -> None:
    engine.start()
    engine.pause()
    assert engine.state == SimState.PAUSED


def test_pause_stopped_raises(engine: SimulationEngine) -> None:
    with pytest.raises(SimulationNotRunningError):
        engine.pause()


def test_advance_when_stopped_raises(engine: SimulationEngine) -> None:
    with pytest.raises(SimulationNotRunningError):
        engine.advance(1)


def test_advance_when_running(engine: SimulationEngine) -> None:
    engine.start()
    snap = engine.advance(3)
    assert engine.tick == 3
    assert snap.total_bikes == 0


def test_stop(engine: SimulationEngine) -> None:
    engine.start()
    engine.stop()
    assert engine.state == SimState.STOPPED


class TestTimeOfDay:
    """time_of_day() should reflect the simulation time within a 24h day."""

    def test_midnight(self, engine: SimulationEngine) -> None:
        engine.start()
        engine.advance(0)
        assert engine.time_of_day() == "00:00"

    def test_early_morning(self, engine: SimulationEngine) -> None:
        engine.start()
        engine.advance(60)
        assert engine.time_of_day() == "01:00"

    def test_noon(self, engine: SimulationEngine) -> None:
        """720 ticks from midnight = 12:00, not 00:00."""
        engine.start()
        engine.advance(720)
        assert engine.time_of_day() == "12:00"

    def test_end_of_day(self, engine: SimulationEngine) -> None:
        engine.start()
        engine.advance(1439)
        assert engine.time_of_day() == "23:59"

    def test_wraps_to_next_day(self, engine: SimulationEngine) -> None:
        """Tick 1440 should be midnight of the next day."""
        engine.start()
        engine.advance(1440)
        assert engine.time_of_day() == "00:00"
        assert engine.day_number == 1
