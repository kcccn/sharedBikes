"""Application and simulation configuration."""

from pydantic_settings import BaseSettings


class SimulationConfig:
    """Configuration for simulation engine behaviour."""

    def __init__(
        self,
        ticks_per_day: int = 1440,
        speed_multiplier: int = 60,
        default_station_capacity: int = 30,
        rebalance_interval_ticks: int = 60,
    ) -> None:
        self.ticks_per_day = ticks_per_day
        self.speed_multiplier = speed_multiplier
        self.default_station_capacity = default_station_capacity
        self.rebalance_interval_ticks = rebalance_interval_ticks


class AppConfig(BaseSettings):
    """Top-level application configuration loaded from environment / .env."""

    sim: SimulationConfig = SimulationConfig()

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    model_config = {"env_prefix": "CITYBIKE_"}
