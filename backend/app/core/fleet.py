"""Fleet model — bike lifecycle, dock/undock operations and snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import NamedTuple


class BikeStatus(Enum):
    DOCKED = auto()
    IN_USE = auto()
    LOST = auto()
    MAINTENANCE = auto()


class LatLng(NamedTuple):
    lat: float
    lng: float


@dataclass
class Bike:
    """A single bike in the fleet."""

    id: str
    status: BikeStatus = BikeStatus.DOCKED
    station_id: str | None = None
    position: LatLng | None = None
    trip_count: int = 0
    total_distance_km: float = 0.0


@dataclass
class FleetSnapshot:
    """Immutable point-in-time view of the entire fleet."""

    bikes: dict[str, Bike]
    station_inventory: dict[str, list[str]]  # station_id → list of bike_ids
    total_docked: int
    total_in_use: int
    total_lost: int


class BikeNotDockedError(Exception):
    """Raised when trying to undock a bike that is not docked."""


@dataclass
class Fleet:
    """Mutable fleet state — only the engine is allowed to mutate."""

    bikes: dict[str, Bike] = field(default_factory=dict)
    station_inventory: dict[str, list[str]] = field(default_factory=dict)

    def add_bike(self, bike: Bike) -> None:
        self.bikes[bike.id] = bike

    def dock_bike(self, bike_id: str, station_id: str) -> None:
        """Dock *bike_id* at *station_id*.  If already docked elsewhere, undock first."""
        bike = self.bikes.get(bike_id)
        if bike is None:
            return
        # If already docked at a different station, remove from old slot
        if bike.station_id and bike.station_id != station_id:
            self._remove_from_station(bike_id, bike.station_id)
        elif bike.station_id == station_id:
            return  # already here — idempotent
        bike.status = BikeStatus.DOCKED
        bike.station_id = station_id
        self.station_inventory.setdefault(station_id, []).append(bike_id)

    def undock_bike(self, bike_id: str) -> None:
        """Undock *bike_id* from its station and mark it IN_USE."""
        bike = self.bikes.get(bike_id)
        if bike is None:
            raise BikeNotDockedError(f"Bike {bike_id} not found")
        if bike.status != BikeStatus.DOCKED or bike.station_id is None:
            raise BikeNotDockedError(f"Bike {bike_id} is not docked")
        self._remove_from_station(bike_id, bike.station_id)
        bike.status = BikeStatus.IN_USE
        bike.station_id = None

    def snapshot(self) -> FleetSnapshot:
        """Build an immutable snapshot of the current fleet state."""
        bikes_copy = {bid: Bike(**b.__dict__) for bid, b in self.bikes.items()}
        inv_copy = {
            sid: list(bids) for sid, bids in self.station_inventory.items()
        }
        return FleetSnapshot(
            bikes=bikes_copy,
            station_inventory=inv_copy,
            total_docked=sum(
                1 for b in self.bikes.values() if b.status == BikeStatus.DOCKED
            ),
            total_in_use=sum(
                1 for b in self.bikes.values() if b.status == BikeStatus.IN_USE
            ),
            total_lost=sum(
                1 for b in self.bikes.values() if b.status == BikeStatus.LOST
            ),
        )

    def _remove_from_station(self, bike_id: str, station_id: str) -> None:
        inv = self.station_inventory.get(station_id)
        if inv and bike_id in inv:
            inv.remove(bike_id)
