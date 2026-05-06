"""Core-level simulation configuration (no I/O)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationConfig:
    """Configuration for simulation engine behaviour."""

    ticks_per_day: int = 1440
    speed_multiplier: int = 60
    default_station_capacity: int = 30
    rebalance_interval_ticks: int = 60
