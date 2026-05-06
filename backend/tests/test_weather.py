"""Tests for weather / environment models."""

from app.core.weather import Environment, SpecialEvent, WeatherCondition


def test_environment_default() -> None:
    env = Environment()
    assert env.condition == WeatherCondition.CLEAR
    assert env.demand_factor() == 1.0


def test_rainy_demand_factor() -> None:
    env = Environment()
    env.condition = WeatherCondition.RAINY
    assert env.demand_factor() == 0.4


def test_stormy_demand_factor() -> None:
    env = Environment()
    env.condition = WeatherCondition.STORMY
    assert env.demand_factor() == 0.4


def test_snowy_demand_factor() -> None:
    env = Environment()
    env.condition = WeatherCondition.SNOWY
    assert env.demand_factor() == 0.2


def test_special_event_active_expiry() -> None:
    event = SpecialEvent(
        event_id="e1",
        name="Concert",
        station_id="s1",
        radius_km=1.0,
        demand_multiplier=3.0,
        duration_ticks=5,
        remaining_ticks=5,
    )
    assert event.active is True
    for _ in range(5):
        event.tick()
    assert event.active is False


def test_environment_tick_decays_events() -> None:
    env = Environment()
    event = SpecialEvent(
        event_id="e1",
        name="Concert",
        station_id="s1",
        radius_km=1.0,
        duration_ticks=1,
        remaining_ticks=1,
    )
    env.events["e1"] = event
    env.tick()
    assert "e1" not in env.events
