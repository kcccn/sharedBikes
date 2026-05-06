"""City configuration system — load city definitions from YAML files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError

# ---- Data models ----


class LatLngModel(BaseModel):
    lat: float
    lng: float


class BoundingBox(BaseModel):
    min_lat: float
    min_lng: float
    max_lat: float
    max_lng: float


class CityConfig(BaseModel):
    """Configuration for a single city."""

    name: str
    center: LatLngModel
    bounding_box: BoundingBox
    osm_source: Literal["osmnx", "file"] = "osmnx"
    osm_file: str = ""
    station_placement: Literal["grid", "random", "uniform"] = "grid"
    station_spacing_m: int = Field(default=300, ge=50, le=5000)
    station_capacity: int = Field(default=30, ge=1, le=500)

    model_config = {"frozen": True, "extra": "forbid"}


# ---- Loader ----


def _default_config_dir() -> Path:
    """Resolve the config/cities directory relative to the project root."""
    # Walk up from this file to find the repo root (where config/ lives)
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "config" / "cities").is_dir():
            return parent / "config" / "cities"
    # Fallback: assume cwd is repo root
    return Path("config") / "cities"


class CityConfigLoader:
    """Loads and caches city configuration from YAML files.

    Config files are stored in ``config/cities/<city_id>.yml``.
    The active city is selected via the ``CITY`` environment variable.
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        self._config_dir = config_dir or _default_config_dir()
        self._cache: dict[str, CityConfig] = {}

    # ---- public API ----

    def list_cities(self) -> list[str]:
        """Return all available city IDs (file stems in the config dir)."""
        if not self._config_dir.is_dir():
            return []
        return sorted(
            p.stem for p in self._config_dir.iterdir() if p.suffix in {".yml", ".yaml"}
        )

    def load(self, city_id: str | None = None) -> CityConfig:
        """Load a city config by ID.

        If *city_id* is ``None``, read the ``CITY`` environment variable.
        If that is also unset, default to ``"beijing"``.

        Raises
        ------
        CityNotFoundError
            When the city ID does not match any config file.
        CityConfigError
            When the config file exists but is malformed.
        """
        city_id = city_id or os.environ.get("CITY") or "beijing"

        if city_id in self._cache:
            return self._cache[city_id]

        config_path = self._resolve_path(city_id)
        if config_path is None:
            available = ", ".join(self.list_cities()) or "(none)"
            msg = (
                f"City '{city_id}' not found. "
                f"Set CITY=<name> or check config/cities/ for available cities. "
                f"Available: {available}"
            )
            raise CityNotFoundError(city_id, msg)

        try:
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise CityConfigError(city_id, f"Failed to parse {config_path}: {exc}") from exc

        if not isinstance(raw, dict) or "city" not in raw:
            raise CityConfigError(
                city_id, f"{config_path} is missing the top-level 'city' key."
            )

        try:
            config = CityConfig.model_validate(raw["city"])
        except ValidationError as exc:
            raise CityConfigError(city_id, f"Invalid config in {config_path}: {exc}") from exc

        self._cache[city_id] = config
        return config

    def reload(self, city_id: str | None = None) -> CityConfig:
        """Force-reload a city config, bypassing cache."""
        if city_id:
            self._cache.pop(city_id, None)
        return self.load(city_id)

    # ---- internal helpers ----

    def _resolve_path(self, city_id: str) -> Path | None:
        """Return the config file path for *city_id*, or ``None``."""
        for ext in (".yml", ".yaml"):
            candidate = self._config_dir / f"{city_id}{ext}"
            if candidate.is_file():
                return candidate
        return None


# ---- Exceptions ----


class CityNotFoundError(LookupError):
    """Raised when a city config file does not exist."""

    def __init__(self, city_id: str, message: str) -> None:
        self.city_id = city_id
        super().__init__(message)


class CityConfigError(ValueError):
    """Raised when a city config file is malformed."""

    def __init__(self, city_id: str, message: str) -> None:
        self.city_id = city_id
        super().__init__(message)
