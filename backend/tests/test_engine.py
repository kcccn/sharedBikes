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


def test_time_of_day(engine: SimulationEngine) -> None:
    engine.start()
    engine.advance(60)  # 60 ticks = 1 hour
    tod = engine.time_of_day()
    assert tod == "01:00"


def test_time_of_day_does_not_reset_at_noon(engine: SimulationEngine) -> None:
    """Regression test: time_of_day() must not reset at midday.

    With ticks_per_day=1440, tick=720 should yield 12:00, not 00:00.
    """
    engine.start()
    engine.advance(720)  # 720 ticks = 12 hours (noon)
    assert engine.time_of_day() == "12:00"


def test_time_of_day_end_of_day(engine: SimulationEngine) -> None:
    engine.start()
    engine.advance(1439)  # 1439 ticks = 23:59
    assert engine.time_of_day() == "23:59"
    engine.advance(1)  # 1440 ticks → next day 00:00
    assert engine.time_of_day() == "00:00"


def test_day_number(engine: SimulationEngine) -> None:
    engine.start()
    assert engine.day_number == 0
    engine.advance(1440)
    assert engine.day_number == 1
    engine.advance(1440)
    assert engine.day_number == 2
