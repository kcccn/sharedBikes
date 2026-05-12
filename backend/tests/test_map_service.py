"""Tests for MapService with procedural city generation."""

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
display_name = "No Stations City"

[station_generation]
enabled = false
""",
    )
    loader = CityLoader(config_dir=tmp_path)
    svc = MapService(loader=loader)
    city = svc.load_city("test")
    assert len(city.nodes) > 0
    assert len(city.edges) > 0
    # Station generation disabled → no stations
    assert len(city.stations) == 0


def test_map_service_caching(tmp_path: Path) -> None:
    _write_toml(tmp_path, "test.toml", "[city]\ndisplay_name = 'Cached City'")
    loader = CityLoader(config_dir=tmp_path)
    svc = MapService(loader=loader)
    city_a = svc.load_city("test")
    city_b = svc.load_city("test")
    assert city_a is city_b  # same cached object


def test_map_service_clear_cache(tmp_path: Path) -> None:
    _write_toml(tmp_path, "test.toml", "[city]\ndisplay_name = 'Test'")
    loader = CityLoader(config_dir=tmp_path)
    svc = MapService(loader=loader)
    city_a = svc.load_city("test")
    svc.clear_cache()
    city_b = svc.load_city("test")
    assert city_a is not city_b  # new object after clearing


def test_map_service_fallback_to_default() -> None:
    """Without any config, load_city falls back to default procedural city."""
    svc = MapService()
    city = svc.load_city("unknown")
    assert len(city.nodes) > 0
    assert len(city.edges) > 0
    # Default provides station generation
    assert len(city.stations) > 0
