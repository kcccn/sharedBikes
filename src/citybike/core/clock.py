"""
Simulation clock — manages time in the virtual world.

Supports:
  • Variable speed: 1x, 10x, 100x, etc.
  • Pause / resume.
  • Jump-to-timestamp for time-travel debugging.
  • Deterministic: same seed + same schedule = same sequence of ticks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class SimClock:
    """
    Immutable-ish simulation clock.

    Usage:
        clock = SimClock.initial(city_tz="Asia/Shanghai")
        clock = clock.tick(hours=0.5)    # advance by 30 mins
        clock = clock.set_speed(10.0)    # 10x speed
    """

    game_time: datetime              # current in-game datetime
    real_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    speed: float = 1.0               # multiplier (1.0 = real-time)
    paused: bool = False

    # ── Config ─────────────────────────────────────────────────────

    SIM_START: datetime = datetime(2024, 9, 1, 6, 0, 0, tzinfo=timezone.utc)

    @classmethod
    def initial(cls) -> SimClock:
        """Create a clock frozen at 2024-09-01 06:00 UTC."""
        return cls(game_time=cls.SIM_START)

    # ── Tick ───────────────────────────────────────────────────────

    def tick(self, real_seconds: float = 1.0) -> SimClock:
        """
        Advance the clock by a real-time duration, scaled by speed.
        No-op if paused.
        """
        if self.paused:
            return self
        delta = timedelta(seconds=real_seconds * self.speed)
        return SimClock(
            game_time=self.game_time + delta,
            real_start=self.real_start,
            speed=self.speed,
            paused=self.paused,
        )

    def advance(self, sim_hours: float) -> SimClock:
        """Jump forward by a fixed number of in-game hours (for testing / time-travel)."""
        return SimClock(
            game_time=self.game_time + timedelta(hours=sim_hours),
            real_start=self.real_start,
            speed=self.speed,
            paused=self.paused,
        )

    # ── Queries ────────────────────────────────────────────────────

    @property
    def hour_of_day(self) -> int:
        """0-23"""
        return self.game_time.hour

    @property
    def day_of_week(self) -> int:
        """Monday=0 .. Sunday=6"""
        return self.game_time.weekday()

    @property
    def is_weekend(self) -> bool:
        return self.day_of_week >= 5

    @property
    def elapsed_days(self) -> float:
        """Days since simulation start."""
        return (self.game_time - self.SIM_START).total_seconds() / 86400.0

    def format(self) -> str:
        """Human-readable: 'Day 3, 08:30'"""
        day = int(self.elapsed_days) + 1
        return f"Day {day}, {self.game_time.strftime('%H:%M')}"
