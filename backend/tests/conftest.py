"""Shared test fixtures."""

from __future__ import annotations

from collections.abc import Generator

import pytest

from app.config import AppConfig, SimulationConfig
from app.core.city import City, LatLng, Station, Zone, ZoneType
from app.core.fleet import Fleet, Bike, BikeStatus


@pytest.fixture
def default_config() -> AppConfig:
    return AppConfig(debug=True)


@pytest.fixture
def sample_city() -> City:
    """A tiny 3-station city for quick tests."""
    return City(
        name="Testville",
        bounds=(LatLng(39.9, 116.3), LatLng(40.0, 116.5)),
        stations={
            "s1": Station(id="s1", position=LatLng(39.95, 116.35), capacity=20, zone_id="z1"),
            "s2": Station(id="s2", position=LatLng(39.96, 116.40), capacity=30, zone_id="z1"),
            "s3": Station(id="s3", position=LatLng(39.94, 116.45), capacity=15, zone_id="z2"),
        },
        zones={
            "z1": Zone(id="z1", name="Downtown", zone_type=ZoneType.COMMERCIAL, center=LatLng(39.955, 116.375)),
            "z2": Zone(id="z2", name="Suburb", zone_type=ZoneType.RESIDENTIAL, center=LatLng(39.94, 116.45)),
        },
    )


@pytest.fixture
def sample_fleet() -> Fleet:
    fleet = Fleet()
    # 5 bikes at station s1
    for i in range(5):
        bid = f"b{i:04d}"
        fleet.bikes[bid] = Bike(id=bid, status=BikeStatus.DOCKED, station_id="s1")
        fleet.station_inventory.setdefault("s1", []).append(bid)
    return fleet
