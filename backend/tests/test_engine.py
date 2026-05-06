"""Tests for the simulation engine."""

import pytest

from app.config import SimulationConfig
from app.core.city import City, LatLng, Station
from app.core.engine import (
    SimulationEngine,
    SimulationNotRunningError,
    SimState,
)
from app.core.fleet import Bike, BikeStatus, Fleet
from app.core.weather import Environment


@pytest.fixture
def city() -> City:
    s1 = Station("st-001", "Central", LatLng(39.9042, 116.4074), 30)
    s2 = Station("st-002", "North Hub", LatLng(39.9142, 116.4074), 20)
    return City(nodes={}, edges={}, stations={"st-001": s1, "st-002": s2})


@pytest.fixture
def fleet(city: City) -> Fleet:
    f = Fleet()
    for i in range(10):
        f.add_bike(Bike(bike_id=f"b-{i:03d}", station_id="st-001"))
    for i in range(10, 15):
        f.add_bike(Bike(bike_id=f"b-{i:03d}", station_id="st-002"))
    return f


@pytest.fixture
def engine(city: City, fleet: Fleet) -> SimulationEngine:
    return SimulationEngine(
        city=city,
        fleet=fleet,
        env=Environment(),
        config=SimulationConfig(),
    )


def test_initial_state(engine: SimulationEngine) -> None:
    assert engine.state == SimState.STOPPED
    assert engine.tick == 0


def test_start_and_tick(engine: SimulationEngine) -> None:
    engine.start()
    snap = engine.advance(10)
    assert engine.tick == 10
    assert snap.docked == 15  # no trips = all docked


def test_advance_raises_when_stopped(engine: SimulationEngine) -> None:
    with pytest.raises(SimulationNotRunningError):
        engine.advance(1)


def test_pause_and_resume(engine: SimulationEngine) -> None:
    engine.start()
    engine.advance(5)
    engine.pause()
    with pytest.raises(SimulationNotRunningError):
        engine.advance(1)
    engine.resume()
    snap = engine.advance(3)
    assert engine.tick == 8
    assert snap is not None


def test_stop(engine: SimulationEngine) -> None:
    engine.start()
    engine.advance(5)
    engine.stop()
    assert engine.state == SimState.STOPPED


def test_reset(engine: SimulationEngine) -> None:
    engine.start()
    engine.advance(100)
    engine.stop()
    engine.reset()
    assert engine.tick == 0
    assert engine.state == SimState.STOPPED


def test_fleet_snapshot(engine: SimulationEngine) -> None:
    engine.start()
    snap = engine.advance(1)
    assert snap.total_bikes == 15
    assert snap.docked == 15


def test_time_of_day_progression(engine: SimulationEngine) -> None:
    engine.start()
    engine.advance(60)  # 60 ticks = 1 hour at default
    assert engine.env.time_of_day == "01:00"
    engine.advance(60)
    assert engine.env.time_of_day == "02:00"
