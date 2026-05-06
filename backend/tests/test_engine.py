"""Tests for simulation engine."""

from __future__ import annotations

from app.core.engine import SimulationEngine, SimState
from app.core.city import City, LatLng


def test_engine_starts_stopped() -> None:
    city = City(name="Test", bounds=(LatLng(0, 0), LatLng(1, 1)))
    engine = SimulationEngine(city=city)
    assert engine.state == SimState.STOPPED
    assert engine.tick == 0


def test_engine_start_and_tick() -> None:
    city = City(name="Test", bounds=(LatLng(0, 0), LatLng(1, 1)))
    engine = SimulationEngine(city=city)
    engine.start()
    assert engine.state == SimState.RUNNING

    snapshot = engine.advance(5)
    assert engine.tick == 5
    assert snapshot.total_bikes == 0


def test_engine_pause_resume() -> None:
    city = City(name="Test", bounds=(LatLng(0, 0), LatLng(1, 1)))
    engine = SimulationEngine(city=city)
    engine.start()
    engine.advance(3)
    engine.pause()
    assert engine.state == SimState.PAUSED
    # No advancement while paused
    engine.advance(10)
    assert engine.tick == 3


def test_time_of_day() -> None:
    city = City(name="Test", bounds=(LatLng(0, 0), LatLng(1, 1)))
    engine = SimulationEngine(city=city)
    engine.start()
    # tick 0 → 00:00
    assert engine.time_of_day() == "00:00"
    engine.advance(60)  # +1 hour
    assert engine.time_of_day() == "01:00"


def test_day_number() -> None:
    city = City(name="Test", bounds=(LatLng(0, 0), LatLng(1, 1)))
    engine = SimulationEngine(city=city)
    assert engine.day_number() == 1
    engine.tick = 1440
    assert engine.day_number() == 2
