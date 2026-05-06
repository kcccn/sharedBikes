"""Tests for simulation engine."""

import pytest

from app.core.city import City
from app.core.config import SimulationConfig
from app.core.engine import SimulationEngine, SimState, SimulationNotRunningError
from app.core.fleet import Fleet, Bike, BikeStatus


def _minimal_city() -> City:
    return City(nodes={}, edges={}, stations={}, zones={})


def _minimal_fleet() -> Fleet:
    return Fleet(bikes={"b1": Bike(bike_id="b1")})


def test_engine_starts_stopped() -> None:
    engine = SimulationEngine(city=_minimal_city(), fleet=_minimal_fleet())
    assert engine.state == SimState.STOPPED
    assert engine.tick == 0


def test_engine_start() -> None:
    engine = SimulationEngine(city=_minimal_city(), fleet=_minimal_fleet())
    engine.start()
    assert engine.state == SimState.RUNNING


def test_engine_advance_increases_tick() -> None:
    engine = SimulationEngine(city=_minimal_city(), fleet=_minimal_fleet())
    engine.start()
    snapshot = engine.advance(steps=5)
    assert engine.tick == 5
    assert snapshot.total_bikes == 1


def test_engine_advance_raises_when_stopped() -> None:
    engine = SimulationEngine(city=_minimal_city(), fleet=_minimal_fleet())
    with pytest.raises(SimulationNotRunningError):
        engine.advance(steps=1)


def test_engine_pause_resume() -> None:
    engine = SimulationEngine(city=_minimal_city(), fleet=_minimal_fleet())
    engine.start()
    engine.pause()
    assert engine.state == SimState.PAUSED
    engine.resume()
    assert engine.state == SimState.RUNNING


def test_engine_pause_when_stopped_raises() -> None:
    engine = SimulationEngine(city=_minimal_city(), fleet=_minimal_fleet())
    with pytest.raises(SimulationNotRunningError):
        engine.pause()


def test_time_of_day() -> None:
    config = SimulationConfig(ticks_per_day=1440)
    engine = SimulationEngine(
        city=_minimal_city(),
        fleet=_minimal_fleet(),
        config=config,
    )
    # tick 0 → 00:00
    assert engine.time_of_day() == "00:00"
    # manually set tick
    engine._tick = 150  # noqa
    assert engine.time_of_day() == "02:30"


def test_engine_stop() -> None:
    engine = SimulationEngine(city=_minimal_city(), fleet=_minimal_fleet())
    engine.start()
    engine.advance(steps=3)
    engine.stop()
    assert engine.state == SimState.STOPPED
