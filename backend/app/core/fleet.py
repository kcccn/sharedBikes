"""Fleet domain: Bike lifecycle, Fleet aggregate, and Snapshots."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from app.core.city import LatLng, Station


class BikeStatus(enum.Enum):
    IDLE = "idle"
    IN_USE = "in_use"
    LOST = "lost"
    MAINTENANCE = "maintenance"


@dataclass
class Bike:
    """A single bike in the fleet."""

    bike_id: str
    status: BikeStatus = BikeStatus.IDLE
    station_id: str | None = None
    position: LatLng | None = None
    total_trips: int = 0
    total_distance_km: float = 0.0


@dataclass
class FleetSnapshot:
    """Immutable point-in-time snapshot of the entire fleet."""

    bikes: dict[str, Bike]
    station_inventory: dict[str, int]
    total_bikes: int
    active_rides: int
    lost_bikes: int


class Fleet:
    """Mutable fleet aggregate — the single source of truth during simulation."""

    def __init__(self, bikes: dict[str, Bike] | None = None) -> None:
        self._bikes: dict[str, Bike] = bikes or {}
        self._inventory: dict[str, int] = {}

    # ---- inventory management ----

    def dock_bike(self, bike_id: str, station: Station) -> None:
        bike = self._bikes.get(bike_id)
        if bike is None:
            raise ValueError(f"Bike {bike_id} not found")
        # undock from previous station first
        if bike.station_id is not None and bike.station_id != station.station_id:
            self._inventory[bike.station_id] = max(0, self._inventory.get(bike.station_id, 0) - 1)
        bike.station_id = station.station_id
        bike.status = BikeStatus.IDLE
        bike.position = station.position
        self._inventory[station.station_id] = self._inventory.get(station.station_id, 0) + 1

    def undock_bike(self, bike_id: str) -> bool:
        bike = self._bikes.get(bike_id)
        if bike is None or bike.station_id is None:
            return False
        self._inventory[bike.station_id] = max(0, self._inventory.get(bike.station_id, 0) - 1)
        bike.station_id = None
        bike.status = BikeStatus.IN_USE
        return True

    def snapshot(self) -> FleetSnapshot:
        return FleetSnapshot(
            bikes=dict(self._bikes),
            station_inventory=dict(self._inventory),
            total_bikes=len(self._bikes),
            active_rides=sum(1 for b in self._bikes.values() if b.status == BikeStatus.IN_USE),
            lost_bikes=sum(1 for b in self._bikes.values() if b.status == BikeStatus.LOST),
        )

    @property
    def bikes(self) -> dict[str, Bike]:
        return self._bikes

    @property
    def inventory(self) -> dict[str, int]:
        return dict(self._inventory)
