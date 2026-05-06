"""Application configuration via pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class SimulationConfig(BaseSettings):
    """Simulation engine parameters."""

    ticks_per_day: int = 1440  # 1 tick = 1 simulated minute
    speed_multiplier: int = 60  # 1 real second = 60 simulated minutes
    default_bikes_per_station: int = 10
    max_bikes_per_station: int = 40
    starvation_threshold: float = 0.2  # < 20% capacity → starving
    overflow_threshold: float = 0.8  # > 80% capacity → overflowing
    rebalance_interval_ticks: int = 60  # rebalance every 60 ticks (1 hour)


class AppConfig(BaseSettings):
    """Top-level application configuration."""

    app_name: str = "CityBike-Sim"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    simulation: SimulationConfig = SimulationConfig()

    model_config = {"env_prefix": "CITYBIKE_"}


config = AppConfig()
