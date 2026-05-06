"""Fleet management — bike lifecycle, station inventory, utilisation tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple


class BikeStatus(Enum):
    DOCKED = "docked"
    IN_USE = "in_use"
    LOST = "lost"
    DAMAGED = "damaged"


class Bike(NamedTuple):
    """Immutable value object representing a single bike at a point in time."""

    id: str
    status: BikeStatus = BikeStatus.DOCKED
    station_id: str | None = None
    total_trips: int = 0
    total_distance_km: float = 0.0


@dataclass
class FleetSnapshot:
    """Point-in-time view of every bike and every station's inventory."""

    bikes: dict[str, Bike] = field(default_factory=dict)
    station_inventory: dict[str, list[str]] = field(default_factory=dict)
    """station_id → list of bike_ids currently docked there."""

    @property
    def total_bikes(self) -> int:
        return len(self.bikes)

    @property
    def active_bikes(self) -> int:
        return sum(1 for b in self.bikes.values() if b.status == BikeStatus.IN_USE)

    def utilisation_rate(self) -> float:
        """Fraction of total bikes currently in use (turnover proxy)."""
        if not self.bikes:
            return 0.0
        return self.active_bikes / self.total_bikes


class BikeNotFoundError(ValueError):
    """Raised when an operation references a non-existent bike."""


class BikeNotDockedError(ValueError):
    """Raised when undocking a bike that is not currently docked."""


@dataclass
class Fleet:
    """Mutable fleet state — the single source of truth during a simulation run."""

    bikes: dict[str, Bike] = field(default_factory=dict)
    station_inventory: dict[str, list[str]] = field(default_factory=dict)

    def snapshot(self) -> FleetSnapshot:
        return FleetSnapshot(
            bikes=dict(self.bikes),
            station_inventory={k: list(v) for k, v in self.station_inventory.items()},
        )

    def dock_bike(self, bike_id: str, station_id: str) -> None:
        """
        Dock *bike_id* at *station_id*.

        If the bike is already docked at another station it is undocked first,
        making this operation idempotent with respect to inventory integrity.
        """
        if bike_id not in self.bikes:
            raise BikeNotFoundError(bike_id)
        # Undock from previous station first to avoid duplicates
        self.undock_bike(bike_id)
        bike = self.bikes[bike_id]
        self.bikes[bike_id] = bike._replace(
            status=BikeStatus.DOCKED, station_id=station_id
        )
        self.station_inventory.setdefault(station_id, []).append(bike_id)

    def undock_bike(self, bike_id: str) -> str | None:
        """
        Remove *bike_id* from its station and mark it IN_USE.

        Returns the previous station_id, or ``None`` if the bike was not
        docked at any station.

        Raises ``BikeNotFoundError`` if the bike does not exist.
        Raises ``BikeNotDockedError`` if the bike is LOST or DAMAGED.
        """
        bike = self.bikes.get(bike_id)
        if bike is None:
            raise BikeNotFoundError(bike_id)

        if bike.status not in (BikeStatus.DOCKED, BikeStatus.IN_USE):
            raise BikeNotDockedError(
                f"Bike {bike_id} is {bike.status.value}, cannot undock"
            )

        if bike.station_id is None:
            return None

        old = bike.station_id
        self.bikes[bike_id] = bike._replace(status=BikeStatus.IN_USE, station_id=None)
        inv = self.station_inventory.get(old, [])
        if bike_id in inv:
            inv.remove(bike_id)
        return old
