"""Tests for simulation engine."""

import pytest

from app.core.city import City, LatLng, Station
from app.core.engine import DailyReport, SimulationEngine, SimulationNotRunningError, SimState
from app.core.fleet import Bike, Fleet
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


@pytest.fixture
def engine_with_stations() -> SimulationEngine:
    """Engine with 2 stations and some bikes, for integration tests."""
    stations = {
        "s1": Station(station_id="s1", position=LatLng(0, 0), capacity=30),
        "s2": Station(station_id="s2", position=LatLng(0.1, 0.1), capacity=30),
    }
    city = City(nodes={}, edges={}, stations=stations, zones={})
    fleet = Fleet()
    # 10 bikes at s1 (overflowing w/ 33%)
    for i in range(10):
        fleet.add_bike(Bike(bike_id=f"b{i}", station_id="s1"))
    # 1 bike at s2 (starving w/ 3%)
    fleet.add_bike(Bike(bike_id="b10", station_id="s2"))
    env = Environment()
    strategy = GreedyThresholdStrategy()
    return SimulationEngine(
        city=city,
        fleet=fleet,
        environment=env,
        strategy=strategy,
        rebalance_interval=60,
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


# ── Phase 3: rebalance integration tests ────────────────────────


def test_rebalance_triggers_on_rebalance_interval(engine_with_stations: SimulationEngine) -> None:
    """Rebalance should trigger at tick % rebalance_interval == 0."""
    engine = engine_with_stations
    engine.start()

    # Advance to tick 59 — no rebalance yet
    engine.advance(59)
    assert engine.tick == 59
    # No dispatch movements should have happened yet
    recent = engine.recent_events
    all_dispatch = sum(len(e.dispatch_movements) for e in recent)
    assert all_dispatch == 0

    # Advance to tick 60 — rebalance should fire
    engine.advance(1)
    assert engine.tick == 60
    events_at_60 = engine.recent_events[-1]
    assert len(events_at_60.dispatch_movements) > 0


def test_rebalance_moves_bikes_from_overflowing_to_starving(
    engine_with_stations: SimulationEngine,
) -> None:
    """After rebalance, bikes should move from overflowing s1 to starving s2."""
    engine = engine_with_stations
    engine.start()

    # Before rebalance
    assert len(engine.fleet.bikes_at_station("s1")) == 10
    assert len(engine.fleet.bikes_at_station("s2")) == 1

    # Advance to rebalance tick
    engine.advance(60)
    events = engine.recent_events[-1]

    # At least one bike should have moved
    assert len(events.dispatch_movements) > 0
    # Some bikes should now be at s2
    assert len(engine.fleet.bikes_at_station("s2")) > 1


def test_rebalance_posts_ledger_entries(engine_with_stations: SimulationEngine) -> None:
    """Rebalance should create dispatch cost + fee ledger entries."""
    engine = engine_with_stations
    engine.start()
    engine.advance(60)

    # Check ledger for dispatch entries
    entries = engine.ledger.entries  # type: ignore[union-attr]
    dispatch_costs = [e for e in entries if "cost-dispatch" in e.entry_id]
    dispatch_fees = [e for e in entries if "rev-dispatch-fee" in e.entry_id]

    assert len(dispatch_costs) > 0
    assert len(dispatch_fees) > 0


def test_rebalance_no_stations_skips(engine: SimulationEngine) -> None:
    """Engine with no stations should skip rebalance gracefully."""
    engine.start()
    engine.advance(60)
    # No stations → no rebalance → no dispatch movements
    events = engine.recent_events[-1]
    assert len(events.dispatch_movements) == 0


def test_daily_report_includes_dispatch(engine_with_stations: SimulationEngine) -> None:
    """DailyReport should include dispatch_count_total."""
    engine = engine_with_stations
    engine.start()

    # Tick every 60 for rebalance, run for a full day
    engine.advance(1440)

    # Check daily reports
    reports = engine.daily_reports
    assert len(reports) >= 1

    # At least one report should show dispatch activity
    dispatch_days = [r for r in reports if r.dispatch_count_total > 0]
    assert len(dispatch_days) > 0, "Rebalancing ran but no dispatch recorded in report"
