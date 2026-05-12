"""Tests for city configuration system."""

from pathlib import Path

import pytest

from app.core.city_config import CityConfig, ProceduralConfig, StationGenerationConfig
from app.services.city_loader import CityLoader, CityLoadError


def _write_toml(dir_path: Path, filename: str, content: str) -> Path:
    p = dir_path / filename
    p.write_text(content, encoding="utf-8")
    return p


class TestCityConfigModel:
    """CityConfig dataclass construction and defaults."""

    def test_minimal_config(self) -> None:
        cfg = CityConfig(city_id="test_city")
        assert cfg.city_id == "test_city"
        assert cfg.display_name == "test_city"  # falls back to city_id
        assert cfg.station_generation.enabled is True
        assert cfg.procedural.grid_rows == 35
        assert cfg.procedural.grid_cols == 35

    def test_full_config(self) -> None:
        cfg = CityConfig(
            city_id="default",
            display_name="Default City",
            country="",
            timezone="UTC",
            default_station_capacity=40,
            initial_bikes_per_station=15,
            ticks_per_day=2880,
            total_bikes=10_000,
            peak_hour_multiplier=4.0,
            off_peak_multiplier=0.2,
            procedural=ProceduralConfig(
                grid_rows=50,
                grid_cols=50,
                spacing=2.0,
                jitter=0.5,
            ),
            station_generation=StationGenerationConfig(
                enabled=True,
                min_distance_km=0.2,
                min_capacity=5,
                max_capacity=60,
                max_stations=500,
            ),
            zone_configs=(
                {"zone_id": "z1", "name": "Center", "polygon": []},
            ),
        )
        assert cfg.procedural.grid_rows == 50
        assert cfg.procedural.grid_cols == 50
        assert cfg.procedural.spacing == 2.0
        assert cfg.procedural.jitter == 0.5
        assert len(cfg.zone_configs) == 1


class TestCityLoader:
    """CityLoader — TOML parsing and file discovery."""

    def test_list_available_empty_dir(self, tmp_path: Path) -> None:
        loader = CityLoader(config_dir=tmp_path)
        assert loader.list_available_cities() == []

    def test_list_available_finds_tomls(self, tmp_path: Path) -> None:
        _write_toml(tmp_path, "default.toml", "[city]\ndisplay_name = 'Default'")
        _write_toml(tmp_path, "custom.toml", "[city]\ndisplay_name = 'Custom'")
        loader = CityLoader(config_dir=tmp_path)
        cities = loader.list_available_cities()
        assert cities == ["custom", "default"]

    def test_load_missing_raises(self, tmp_path: Path) -> None:
        loader = CityLoader(config_dir=tmp_path)
        with pytest.raises(CityLoadError, match="not found"):
            loader.load("nonexistent")

    def test_load_invalid_toml_raises(self, tmp_path: Path) -> None:
        _write_toml(tmp_path, "bad.toml", "[[[invalid]]]")
        loader = CityLoader(config_dir=tmp_path)
        with pytest.raises(CityLoadError, match="Invalid TOML"):
            loader.load("bad")

    def test_load_minimal_config(self, tmp_path: Path) -> None:
        _write_toml(
            tmp_path,
            "test.toml",
            "[city]\ndisplay_name = 'Test City'\ntotal_bikes = 100\n",
        )
        loader = CityLoader(config_dir=tmp_path)
        cfg = loader.load("test")
        assert cfg.city_id == "test"
        assert cfg.display_name == "Test City"
        assert cfg.total_bikes == 100
        assert cfg.station_generation.enabled is True  # default
        assert cfg.procedural.grid_rows == 35  # default

    def test_load_with_procedural_config(self, tmp_path: Path) -> None:
        _write_toml(
            tmp_path,
            "custom.toml",
            """
[city]
display_name = "Custom City"
total_bikes = 2000
default_station_capacity = 40

[procedural]
grid_rows = 50
grid_cols = 60
spacing = 2.0
jitter = 0.3

[station_generation]
enabled = true
min_distance_km = 0.2
max_stations = 300
""",
        )
        loader = CityLoader(config_dir=tmp_path)
        cfg = loader.load("custom")
        assert cfg.city_id == "custom"
        assert cfg.total_bikes == 2000
        assert cfg.procedural.grid_rows == 50
        assert cfg.procedural.grid_cols == 60
        assert cfg.procedural.spacing == 2.0
        assert cfg.procedural.jitter == 0.3
        assert cfg.station_generation.min_distance_km == 0.2
        assert cfg.station_generation.max_stations == 300

    def test_load_all(self, tmp_path: Path) -> None:
        _write_toml(tmp_path, "a.toml", "[city]\ndisplay_name = 'A'")
        _write_toml(tmp_path, "b.toml", "[city]\ndisplay_name = 'B'")
        loader = CityLoader(config_dir=tmp_path)
        all_cfgs = loader.load_all()
        assert set(all_cfgs) == {"a", "b"}
