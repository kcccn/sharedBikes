"""Application and simulation configuration."""

from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """Top-level application configuration loaded from environment / .env."""

    city: str = "beijing"

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    model_config = {"env_prefix": "CITYBIKE_"}
