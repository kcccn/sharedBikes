"""Tests for the simulation engine."""

import pytest

from backend.engine import SimulationConfig, SimulationEngine


@pytest.fixture
def engine():
    config = SimulationConfig(city_name="test-city", total_bikes=10)
    eng = SimulationEngine(config)
    eng.initialize()
    return eng


def test_engine_initialization(engine: SimulationEngine):
    assert len(engine.bikes) == 10
    assert engine.state.total_bikes == 10
    assert engine.state.day == 1
    assert engine.state.hour == 8


def test_engine_tick(engine: SimulationEngine):
    initial_hour = engine.state.hour
    for _ in range(60):
        engine.tick()
    # After 60 ticks, hour should advance by 1 (every 60 ticks)
    assert engine.state.hour == (initial_hour + 1) % 24
    assert engine._tick == 60


def test_engine_run(engine: SimulationEngine):
    states = []
    engine.run(10, lambda s: states.append(s))
    assert len(states) == 10
    assert engine._tick == 10
