"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings


class SimulationConfig(BaseSettings):
    """Core simulation parameters."""

    # Simulation timing (1 tick = speed_multiplier real seconds)
    speed_multiplier: int = 60  # 1 tick = 1 simulated minute at 1x
    ticks_per_hour: int = 60
    max_ticks: int = 100_000

    # Fleet defaults
    default_bike_count: int = 500
    max_bikes_per_station: int = 40

    # Weather
    weather_update_interval: int = 60  # ticks between weather updates

    model_config = {"env_prefix": "SIM_", "frozen": True}


class AppConfig(BaseSettings):
    """API server configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"

    simulation: SimulationConfig = SimulationConfig()

    model_config = {"env_prefix": "APP_", "frozen": True}
