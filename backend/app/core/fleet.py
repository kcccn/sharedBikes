"""Fleet & Bike domain model — mutable simulation state."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from app.core.city import LatLng


class BikeStatus(Enum):
    """Lifecycle state of a bike."""

    DOCKED = auto()
    IN_USE = auto()
    LOST = auto()
    MAINTENANCE = auto()


@dataclass
class Bike:
    """A single bicycle in the fleet."""

    bike_id: str
    status: BikeStatus = BikeStatus.DOCKED
    station_id: str | None = None
    rider_id: str | None = None
    total_trips: int = 0
    total_distance_km: float = 0.0


class BikeNotFoundError(KeyError):
    """Raised when a bike_id does not exist in the fleet."""


class BikeNotDockedError(ValueError):
    """Raised when trying to undock a bike that is not docked."""


@dataclass
class Fleet:
    """Mutable fleet state — all bikes currently in the simulation."""

    bikes: dict[str, Bike] = field(default_factory=dict)

    # ── queries ──────────────────────────────────────────

    def get_bike(self, bike_id: str) -> Bike | None:
        return self.bikes.get(bike_id)

    def count_docked(self, station_id: str) -> int:
        return sum(
            1 for b in self.bikes.values()
            if b.status == BikeStatus.DOCKED and b.station_id == station_id
        )

    def count_status(self, status: BikeStatus) -> int:
        return sum(1 for b in self.bikes.values() if b.status == status)

    # ── mutations ────────────────────────────────────────

    def add_bike(self, bike: Bike) -> None:
        self.bikes[bike.bike_id] = bike

    def dock_bike(self, bike_id: str, station_id: str) -> None:
        """Park *bike_id* at *station_id*.

        If the bike was previously docked elsewhere it is moved;
        if already at *station_id* the call is a no-op.
        """
        bike = self.bikes.get(bike_id)
        if bike is None:
            raise BikeNotFoundError(bike_id)
        if bike.station_id == station_id and bike.status == BikeStatus.DOCKED:
            return  # idempotent
        bike.station_id = station_id
        bike.status = BikeStatus.DOCKED
        bike.rider_id = None

    def undock_bike(self, bike_id: str, rider_id: str) -> LatLng | None:
        """Remove a bike from its station and assign to a rider.

        Returns the bike's last known station position, or *None* if the
        bike was not docked.
        """
        bike = self.bikes.get(bike_id)
        if bike is None:
            raise BikeNotFoundError(bike_id)
        if bike.status != BikeStatus.DOCKED or bike.station_id is None:
            raise BikeNotDockedError(
                f"Bike {bike_id} is {bike.status.name}, cannot undock"
            )
        # We don't have the station position here; caller gets it from City
        bike.status = BikeStatus.IN_USE
        bike.rider_id = rider_id
        station_id = bike.station_id
        bike.station_id = None
        return station_id

    def mark_lost(self, bike_id: str) -> None:
        bike = self.bikes.get(bike_id)
        if bike is None:
            raise BikeNotFoundError(bike_id)
        bike.status = BikeStatus.LOST

    def snapshot(self) -> FleetSnapshot:
        """Return an immutable view of the current fleet state."""
        return FleetSnapshot(
            total_bikes=len(self.bikes),
            docked=self.count_status(BikeStatus.DOCKED),
            in_use=self.count_status(BikeStatus.IN_USE),
            lost=self.count_status(BikeStatus.LOST),
            maintenance=self.count_status(BikeStatus.MAINTENANCE),
            station_counts={
                sid: self.count_docked(sid)
                for sid in {b.station_id for b in self.bikes.values() if b.station_id}
            },
        )


@dataclass(frozen=True)
class FleetSnapshot:
    """Immutable point-in-time view of fleet-wide metrics."""

    total_bikes: int
    docked: int
    in_use: int
    lost: int
    maintenance: int
    station_counts: dict[str, int]  # station_id → docked count
