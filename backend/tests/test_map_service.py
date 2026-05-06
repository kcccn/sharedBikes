"""Tests for MapService with city config integration."""

from pathlib import Path

from app.services.city_loader import CityLoader
from app.services.map_service import MapService


def _write_toml(dir_path: Path, filename: str, content: str) -> Path:
    p = dir_path / filename
    p.write_text(content, encoding="utf-8")
    return p


def test_map_service_list_cities(tmp_path: Path) -> None:
    _write_toml(tmp_path, "beijing.toml", "[city]\ndisplay_name = 'Beijing'")
    _write_toml(tmp_path, "shanghai.toml", "[city]\ndisplay_name = 'Shanghai'")
    loader = CityLoader(config_dir=tmp_path)
    svc = MapService(loader=loader)
    assert svc.list_available_cities() == ["beijing", "shanghai"]


def test_map_service_load_city_builds_network(tmp_path: Path) -> None:
    _write_toml(
        tmp_path,
        "test.toml",
        """
[city]
display_name = "Test City"
total_bikes = 100

[station_generation]
enabled = true
min_distance_km = 0.3
max_stations = 5
""",
    )
    loader = CityLoader(config_dir=tmp_path)
    svc = MapService(loader=loader)
    city = svc.load_city("test")
    assert city.city_id == "test"  # type check — City has _nodes etc
    assert len(city.nodes) > 0
    assert len(city.edges) > 0
    # Station generation should have produced stations
    assert len(city.stations) > 0


def test_map_service_load_with_stations_disabled(tmp_path: Path) -> None:
    _write_toml(
        tmp_path,
        "test.toml",
        """
[city]
display_name = "No Stations"

[station_generation]
enabled = false
""",
    )
    loader = CityLoader(config_dir=tmp_path)
    svc = MapService(loader=loader)
    city = svc.load_city("test")
    assert len(city.stations) == 0


def test_map_service_cache_returns_same_object(tmp_path: Path) -> None:
    _write_toml(tmp_path, "cache_test.toml", "[city]\ndisplay_name = 'Cache'")
    loader = CityLoader(config_dir=tmp_path)
    svc = MapService(loader=loader)
    c1 = svc.load_city("cache_test")
    c2 = svc.load_city("cache_test")
    assert c1 is c2  # same object from cache


def test_map_service_clear_cache_reloads(tmp_path: Path) -> None:
    _write_toml(tmp_path, "cc.toml", "[city]\ndisplay_name = 'Clearable'")
    loader = CityLoader(config_dir=tmp_path)
    svc = MapService(loader=loader)
    c1 = svc.load_city("cc")
    svc.clear_cache()
    c2 = svc.load_city("cc")
    assert c1 is not c2


import pytest  # noqa: E402
