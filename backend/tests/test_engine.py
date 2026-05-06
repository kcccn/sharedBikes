"""Tests for the simulation engine."""

from app.core.city import City, Station, LatLng
from app.core.engine import SimulationEngine, SimState
from app.core.fleet import Bike, BikeStatus


def _make_city() -> City:
    s1 = Station("s1", "Alpha", LatLng(0.0, 0.0), 20)
    s2 = Station("s2", "Beta", LatLng(0.001, 0.001), 20)
    return City("test", nodes=(), edges=(), stations=(s1, s2), zones=())


def test_engine_lifecycle() -> None:
    city = _make_city()
    engine = SimulationEngine(city=city)
    assert engine.state == SimState.CREATED

    engine.start()
    assert engine.state == SimState.RUNNING

    engine.pause()
    assert engine.state == SimState.PAUSED

    engine.resume()
    assert engine.state == SimState.RUNNING

    engine.stop()
    assert engine.state == SimState.STOPPED


def test_engine_advance_returns_snapshot() -> None:
    city = _make_city()
    engine = SimulationEngine(city=city)
    engine.fleet.add_bike(Bike("b1", station_id="s1"))
    engine.start()
    snap = engine.advance(steps=5)
    assert snap is not None
    assert snap.tick == 5  # type: ignore[attr-defined]


def test_engine_advance_returns_none_when_not_running() -> None:
    city = _make_city()
    engine = SimulationEngine(city=city)
    result = engine.advance(steps=3)
    assert result is None


def test_time_of_day() -> None:
    city = _make_city()
    engine = SimulationEngine(city=city)
    engine.tick = 150  # 2h30m
    assert engine.time_of_day() == "02:30"
