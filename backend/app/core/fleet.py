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


@dataclass
class Bike(NamedTuple):
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
        bike = self.bikes[bike_id]
        self.bikes[bike_id] = bike._replace(
            status=BikeStatus.DOCKED, station_id=station_id
        )
        self.station_inventory.setdefault(station_id, []).append(bike_id)

    def undock_bike(self, bike_id: str) -> str | None:
        """Remove bike from its station; return old station id or None."""
        bike = self.bikes.get(bike_id)
        if bike is None or bike.station_id is None:
            return None
        old = bike.station_id
        self.bikes[bike_id] = bike._replace(status=BikeStatus.IN_USE, station_id=None)
        inv = self.station_inventory.get(old, [])
        if bike_id in inv:
            inv.remove(bike_id)
        return old
