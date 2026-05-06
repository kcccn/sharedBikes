"""SimulationEngine 单元测试。"""

from __future__ import annotations

from datetime import datetime, timedelta

from citybike.core.engine import SimulationEngine


class TestSimulationEngine:
    def test_initial_state(self, engine: SimulationEngine) -> None:
        assert engine.now == datetime(2025, 1, 1, 6, 0)
        assert engine.speed == 60.0
        assert engine._paused is False

    def test_tick_advances_time(self, engine: SimulationEngine) -> None:
        before = engine.now
        engine.tick(real_seconds=1.0)
        # 1 real sec * 60 speed = 60 simulated min = 1 hour
        assert engine.now == before + timedelta(hours=1)

    def test_pause_resume(self, engine: SimulationEngine) -> None:
        engine.pause()
        before = engine.now
        engine.tick(1.0)
        assert engine.now == before  # no advancement

        engine.resume()
        engine.tick(1.0)
        assert engine.now > before

    def test_set_speed_clamps(self, engine: SimulationEngine) -> None:
        engine.set_speed(0.5)   # below min
        assert engine.speed == 1.0

        engine.set_speed(7200)  # above max
        assert engine.speed == 3600.0

        engine.set_speed(120.0)
        assert engine.speed == 120.0

    def test_schedule_event(self, engine: SimulationEngine) -> None:
        events_triggered: list[int] = []

        def cb() -> None:
            events_triggered.append(1)

        future = engine.now + timedelta(minutes=30)
        engine.schedule(future, cb)
        assert len(engine._events) == 1

        engine.tick(0.5)  # advance 30 min
        assert len(events_triggered) == 1
        assert len(engine._events) == 0
