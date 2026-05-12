"""City loader — reads city configuration from TOML files.

Uses Python 3.11+ built-in ``tomllib``.
"""

from __future__ import annotations

from pathlib import Path

from app.core.city_config import CityConfig, ProceduralConfig, StationGenerationConfig

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]


class CityLoadError(RuntimeError):
    """Raised when city configuration cannot be loaded."""


class CityLoader:
    """Service for loading city configuration from TOML files.

    Config files live in a config directory (default ``data/cities/``)
    and are named ``{city_id}.toml``.
    """

    def __init__(self, config_dir: str | Path = "data/cities") -> None:
        self._config_dir = Path(config_dir)

    def list_available_cities(self) -> list[str]:
        """Return city IDs for which a TOML config exists."""
        if not self._config_dir.is_dir():
            return []
        return sorted(f.stem for f in self._config_dir.glob("*.toml"))

    def load(self, city_id: str) -> CityConfig:
        """Load the config for *city_id* from ``{city_id}.toml``."""
        path = self._config_dir / f"{city_id}.toml"
        if not path.is_file():
            raise CityLoadError(
                f"City config not found: {path} "
                f"(search dir: {self._config_dir.resolve()})"
            )
        return self._parse_toml(path.read_bytes(), city_id)

    def load_all(self) -> dict[str, CityConfig]:
        """Load configurations for all available cities."""
        return {cid: self.load(cid) for cid in self.list_available_cities()}

    # ── internal ───────────────────────────────────────

    def _parse_toml(self, raw: bytes, city_id: str) -> CityConfig:
        try:
            data = tomllib.loads(raw.decode("utf-8"))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
            raise CityLoadError(f"Invalid TOML for '{city_id}': {exc}") from exc

        city = data.get("city", {})
        procedural_raw = data.get("procedural", {})
        station_raw = data.get("station_generation", {})
        zones_raw = data.get("zones", [])

        return CityConfig(
            city_id=city_id,
            display_name=city.get("display_name", city_id),
            country=city.get("country", ""),
            timezone=city.get("timezone", "UTC"),
            default_station_capacity=city.get("default_station_capacity", 30),
            initial_bikes_per_station=city.get("initial_bikes_per_station", 10),
            ticks_per_day=city.get("ticks_per_day", 1440),
            total_bikes=city.get("total_bikes", 500),
            peak_hour_multiplier=city.get("peak_hour_multiplier", 3.0),
            off_peak_multiplier=city.get("off_peak_multiplier", 0.3),
            procedural=ProceduralConfig(
                grid_rows=procedural_raw.get("grid_rows", 35),
                grid_cols=procedural_raw.get("grid_cols", 35),
                spacing=procedural_raw.get("spacing", 1.0),
                jitter=procedural_raw.get("jitter", 0.1),
            ),
            station_generation=StationGenerationConfig(
                enabled=station_raw.get("enabled", True),
                min_distance_km=station_raw.get("min_distance_km", 0.3),
                min_capacity=station_raw.get("min_capacity", 10),
                max_capacity=station_raw.get("max_capacity", 50),
                max_stations=station_raw.get("max_stations"),
            ),
            zone_configs=tuple(zones_raw),
        )


# Convenience singleton
_default_loader: CityLoader | None = None


def get_city_loader(config_dir: str | Path = "data/cities") -> CityLoader:
    """Return the default (cached) CityLoader instance."""
    global _default_loader
    if _default_loader is None:
        _default_loader = CityLoader(config_dir=config_dir)
    return _default_loader
