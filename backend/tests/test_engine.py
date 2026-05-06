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


def test_time_of_day_midnight(engine: SimulationEngine) -> None:
    """Tick 0 should be 00:00 (midnight start)."""
    assert engine.time_of_day() == "00:00"


def test_time_of_day_one_hour(engine: SimulationEngine) -> None:
    """60 ticks = 1 hour → 01:00."""
    engine.start()
    engine.advance(60)
    assert engine.time_of_day() == "01:00"


def test_time_of_day_noon(engine: SimulationEngine) -> None:
    """720 ticks = 12 hours → 12:00 (noon), not a reset to 00:00."""
    engine.start()
    engine.advance(720)
    assert engine.time_of_day() == "12:00"


def test_time_of_day_afternoon(engine: SimulationEngine) -> None:
    """780 ticks = 13 hours → 13:00, not a reset to 01:00."""
    engine.start()
    engine.advance(780)
    assert engine.time_of_day() == "13:00"


def test_time_of_day_end_of_day(engine: SimulationEngine) -> None:
    """1439 ticks = 23:59 (last minute of the day)."""
    engine.start()
    engine.advance(1439)
    assert engine.time_of_day() == "23:59"


def test_time_of_day_wraps_to_next_day(engine: SimulationEngine) -> None:
    """1440 ticks = full day → wraps to 00:00 (next midnight)."""
    engine.start()
    engine.advance(1440)
    assert engine.time_of_day() == "00:00"
    assert engine.day_number == 1


def test_time_of_day_multi_day(engine: SimulationEngine) -> None:
    """1500 ticks = day 1, 01:00 (one hour into the second day)."""
    engine.start()
    engine.advance(1500)
    assert engine.time_of_day() == "01:00"
    assert engine.day_number == 1
