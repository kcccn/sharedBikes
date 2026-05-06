"""Tests for the city configuration system."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

import pytest
import yaml

from app.core.city_config import (
    BoundingBox,
    CityConfig,
    CityConfigError,
    CityConfigLoader,
    CityNotFoundError,
    LatLngModel,
)


# ---- helpers ----


@pytest.fixture
def tmp_config_dir(tmp_path: Path) -> Iterator[Path]:
    """Provide a temporary config/cities directory with a beijing.yml sample."""
    cities_dir = tmp_path / "config" / "cities"
    cities_dir.mkdir(parents=True)

    sample = {
        "city": {
            "name": "北京",
            "center": {"lat": 39.9042, "lng": 116.4074},
            "bounding_box": {
                "min_lat": 39.80,
                "min_lng": 116.20,
                "max_lat": 40.00,
                "max_lng": 116.60,
            },
            "osm_source": "osmnx",
            "station_placement": "grid",
            "station_spacing_m": 300,
            "station_capacity": 30,
        }
    }
    (cities_dir / "beijing.yml").write_text(yaml.dump(sample), encoding="utf-8")
    yield cities_dir


# ---- CityConfig Pydantic model ----


class TestCityConfigModel:
    def test_valid_config(self) -> None:
        cfg = CityConfig(
            name="上海",
            center=LatLngModel(lat=31.2304, lng=121.4737),
            bounding_box=BoundingBox(
                min_lat=31.10, min_lng=121.30, max_lat=31.35, max_lng=121.60
            ),
            osm_source="osmnx",
            station_placement="grid",
            station_spacing_m=400,
            station_capacity=20,
        )
        assert cfg.name == "上海"
        assert cfg.center.lat == 31.2304
        assert cfg.station_spacing_m == 400

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValueError):
            CityConfig(
                name="Test",
                center=LatLngModel(lat=0, lng=0),
                bounding_box=BoundingBox(min_lat=0, min_lng=0, max_lat=1, max_lng=1),
                osm_source="osmnx",
                station_placement="grid",
                station_spacing_m=300,
                station_capacity=30,
                unknown_field="nope",  # type: ignore[call-arg]
            )

    def test_invalid_osm_source(self) -> None:
        with pytest.raises(ValueError):
            CityConfig(
                name="Test",
                center=LatLngModel(lat=0, lng=0),
                bounding_box=BoundingBox(min_lat=0, min_lng=0, max_lat=1, max_lng=1),
                osm_source="invalid",  # type: ignore[arg-type]
                station_placement="grid",
                station_spacing_m=300,
                station_capacity=30,
            )

    def test_station_spacing_bounds(self) -> None:
        with pytest.raises(ValueError):
            CityConfig(
                name="Test",
                center=LatLngModel(lat=0, lng=0),
                bounding_box=BoundingBox(min_lat=0, min_lng=0, max_lat=1, max_lng=1),
                osm_source="osmnx",
                station_placement="grid",
                station_spacing_m=0,
                station_capacity=30,
            )

    def test_station_capacity_bounds(self) -> None:
        with pytest.raises(ValueError):
            CityConfig(
                name="Test",
                center=LatLngModel(lat=0, lng=0),
                bounding_box=BoundingBox(min_lat=0, min_lng=0, max_lat=1, max_lng=1),
                osm_source="osmnx",
                station_placement="grid",
                station_spacing_m=300,
                station_capacity=0,
            )


# ---- CityConfigLoader ----


class TestCityConfigLoader:
    def test_load_by_id(self, tmp_config_dir: Path) -> None:
        loader = CityConfigLoader(config_dir=tmp_config_dir)
        cfg = loader.load("beijing")
        assert isinstance(cfg, CityConfig)
        assert cfg.name == "北京"

    def test_load_defaults_to_beijing(self, tmp_config_dir: Path) -> None:
        loader = CityConfigLoader(config_dir=tmp_config_dir)
        cfg = loader.load()
        assert cfg.name == "北京"

    def test_load_uses_env_var(self, tmp_config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Create a second city config
        shanghai = {
            "city": {
                "name": "上海",
                "center": {"lat": 31.2304, "lng": 121.4737},
                "bounding_box": {
                    "min_lat": 31.10, "min_lng": 121.30,
                    "max_lat": 31.35, "max_lng": 121.60,
                },
                "osm_source": "osmnx",
                "station_placement": "grid",
                "station_spacing_m": 300,
                "station_capacity": 30,
            }
        }
        (tmp_config_dir / "shanghai.yml").write_text(yaml.dump(shanghai), encoding="utf-8")
        monkeypatch.setenv("CITY", "shanghai")

        loader = CityConfigLoader(config_dir=tmp_config_dir)
        cfg = loader.load()
        assert cfg.name == "上海"

    def test_load_nonexistent_raises(self, tmp_config_dir: Path) -> None:
        loader = CityConfigLoader(config_dir=tmp_config_dir)
        with pytest.raises(CityNotFoundError) as exc_info:
            loader.load("nonexistent")
        assert "nonexistent" in str(exc_info.value)

    def test_load_malformed_file_raises(self, tmp_config_dir: Path) -> None:
        (tmp_config_dir / "bad.yml").write_text("not: valid: yaml: [", encoding="utf-8")
        loader = CityConfigLoader(config_dir=tmp_config_dir)
        with pytest.raises(CityConfigError):
            loader.load("bad")

    def test_load_missing_city_key_raises(self, tmp_config_dir: Path) -> None:
        (tmp_config_dir / "bad.yml").write_text("foo: bar", encoding="utf-8")
        loader = CityConfigLoader(config_dir=tmp_config_dir)
        with pytest.raises(CityConfigError, match="missing the top-level 'city' key"):
            loader.load("bad")

    def test_load_caches_result(self, tmp_config_dir: Path) -> None:
        loader = CityConfigLoader(config_dir=tmp_config_dir)
        cfg1 = loader.load("beijing")
        cfg2 = loader.load("beijing")
        assert cfg1 is cfg2  # same cached object

    def test_reload_bypasses_cache(self, tmp_config_dir: Path) -> None:
        loader = CityConfigLoader(config_dir=tmp_config_dir)
        cfg1 = loader.load("beijing")
        cfg2 = loader.reload("beijing")
        assert cfg1 is not cfg2  # new object

    def test_list_cities(self, tmp_config_dir: Path) -> None:
        (tmp_config_dir / "shanghai.yml").write_text(
            "city:\n  name: 上海\n  center: {lat: 0, lng: 0}\n"
            "  bounding_box: {min_lat: 0, min_lng: 0, max_lat: 1, max_lng: 1}\n"
            "  station_placement: grid\n  station_spacing_m: 300\n  station_capacity: 30\n",
            encoding="utf-8",
        )
        loader = CityConfigLoader(config_dir=tmp_config_dir)
        cities = loader.list_cities()
        assert "beijing" in cities
        assert "shanghai" in cities

    def test_list_cities_empty_dir(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        loader = CityConfigLoader(config_dir=empty_dir)
        assert loader.list_cities() == []

    def test_list_cities_nonexistent_dir(self) -> None:
        loader = CityConfigLoader(config_dir=Path("/nonexistent/path"))
        assert loader.list_cities() == []

    def test_friendly_error_message_includes_available(self, tmp_config_dir: Path) -> None:
        loader = CityConfigLoader(config_dir=tmp_config_dir)
        try:
            loader.load("paris")
        except CityNotFoundError as exc:
            msg = str(exc)
            assert "paris" in msg
            assert "beijing" in msg  # hints the available city

    def test_yaml_extension_support(self, tmp_config_dir: Path) -> None:
        """Both .yml and .yaml should work."""
        (tmp_config_dir / "shanghai.yaml").write_text(
            "city:\n  name: 上海\n  center: {lat: 0, lng: 0}\n"
            "  bounding_box: {min_lat: 0, min_lng: 0, max_lat: 1, max_lng: 1}\n"
            "  station_placement: grid\n  station_spacing_m: 300\n  station_capacity: 30\n",
            encoding="utf-8",
        )
        loader = CityConfigLoader(config_dir=tmp_config_dir)
        cfg = loader.load("shanghai")
        assert cfg.name == "上海"
        cities = loader.list_cities()
        assert "shanghai" in cities
