"""Fleet state: bikes and their life-cycle."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple


class BikeStatus(Enum):
    DOCKED = "docked"
    IN_USE = "in_use"
    LOST = "lost"
    MAINTENANCE = "maintenance"


class LatLng(NamedTuple):
    lat: float
    lng: float


@dataclass
class Bike:
    """A single bike in the fleet."""

    bike_id: str
    status: BikeStatus = BikeStatus.DOCKED
    station_id: str | None = None
    position: LatLng | None = None
    total_trips: int = 0
    total_distance_km: float = 0.0


@dataclass
class FleetSnapshot:
    """Immutable point-in-time view of the entire fleet."""

    bikes: tuple[Bike, ...]
    station_inventory: dict[str, int]  # station_id → bike count
    total_bikes: int
    active_trips: int
    bikes_docked: int

    @property
    def utilization(self) -> float:
        if self.total_bikes == 0:
            return 0.0
        return self.active_trips / self.total_bikes


@dataclass
class Fleet:
    """Mutable fleet state.  Apply mutations then snapshot for consumers."""

    bikes: dict[str, Bike] = field(default_factory=dict)

    def add_bike(self, bike: Bike) -> None:
        self.bikes[bike.bike_id] = bike

    def dock_bike(self, bike_id: str, station_id: str) -> None:
        bike = self.bikes.get(bike_id)
        if bike is None:
            return
        bike.status = BikeStatus.DOCKED
        bike.station_id = station_id
        bike.position = None

    def undock_bike(self, bike_id: str) -> Bike | None:
        bike = self.bikes.get(bike_id)
        if bike is None or bike.status != BikeStatus.DOCKED:
            return None
        bike.status = BikeStatus.IN_USE
        bike.station_id = None
        return bike

    def snapshot(self) -> FleetSnapshot:
        bikes = tuple(self.bikes.values())
        inventory: dict[str, int] = {}
        active = 0
        docked = 0
        for b in bikes:
            if b.status == BikeStatus.DOCKED and b.station_id:
                inventory[b.station_id] = inventory.get(b.station_id, 0) + 1
                docked += 1
            elif b.status == BikeStatus.IN_USE:
                active += 1
        return FleetSnapshot(
            bikes=bikes,
            station_inventory=inventory,
            total_bikes=len(bikes),
            active_trips=active,
            bikes_docked=docked,
        )
