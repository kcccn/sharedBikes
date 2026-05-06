"""Pytest 共享 fixtures。"""

from __future__ import annotations

import pytest

from citybike.core.engine import SimulationEngine
from citybike.core.types import Bike, BikeStatus, GeoPoint


@pytest.fixture
def engine() -> SimulationEngine:
    return SimulationEngine()


@pytest.fixture
def sample_bike() -> Bike:
    return Bike(
        bike_id="test-bike-001",
        status=BikeStatus.IDLE,
        position=GeoPoint(39.9042, 116.4074),
    )
