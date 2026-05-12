"""Map service — loads and caches City from procedural generation.

The old OSM/LatLng pipeline has been removed. All cities are now
generated procedurally from configuration parameters. The only supported
source type is ``"mock"`` (procedural).

See also
--------
- :class:`app.services.procedural_city_generator.ProceduralCityGenerator`
  for the abstract city generation algorithm.
"""

from __future__ import annotations

from pathlib import Path

from app.core.city import City, Coord, Node, Station, Zone
from app.core.city_config import CityConfig
from app.services.city_loader import CityLoader, CityLoadError
from app.services.procedural_city_generator import ProceduralCityGenerator


class MapService:
    """Service responsible for loading city map data."""

    def __init__(
        self,
        loader: CityLoader | None = None,
        data_dir: str | Path = "data",
    ) -> None:
        self._loader = loader or CityLoader(config_dir=Path(data_dir) / "cities")
        self._cache: dict[str, City] = {}

    # ── Public API ───────────────────────────────────────────────────

    def list_available_cities(self) -> list[str]:
        """Return city IDs for which configuration exists."""
        return self._loader.list_available_cities()

    def load_city(self, city_id: str) -> City:
        """Load (or return cached) City for *city_id*.

        1. Try loading from TOML config (config-driven procedural generation).
        2. Fallback: return a minimal default procedural city (never crashes).
        """
        if city_id in self._cache:
            return self._cache[city_id]

        # Strategy 1: Config-driven pipeline
        try:
            config = self._loader.load(city_id)
            city = self._build_city(config)
            self._cache[city_id] = city
            return city
        except CityLoadError:
            pass

        # Strategy 2: Default procedural city
        city = self._build_default_city(city_id)
        self._cache[city_id] = city
        return city

    # ── Config-driven pipeline ───────────────────────────────────────

    def _build_city(self, config: CityConfig) -> City:
        """Construct a ``City`` from its configuration using procedural generation."""
        generator = ProceduralCityGenerator(
            seed=hash(config.city_id) % (2**31),
            grid_rows=config.procedural.grid_rows,
            grid_cols=config.procedural.grid_cols,
            spacing=config.procedural.spacing,
            jitter=config.procedural.jitter,
        )
        return generator.generate(config)

    # ── Fallback ─────────────────────────────────────────────────────

    @staticmethod
    def _build_default_city(name: str) -> City:
        """Return a minimal default procedural city."""
        generator = ProceduralCityGenerator(
            seed=hash(name) % (2**31),
            grid_rows=10,
            grid_cols=10,
            spacing=2.0,
        )
        return generator.generate()

    # ── Cache control ────────────────────────────────────────────────

    def clear_cache(self) -> None:
        """Invalidate the in-memory city cache."""
        self._cache.clear()
