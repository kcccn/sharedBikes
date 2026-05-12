"""Fleet management: Bike lifecycle and FleetSnapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from app.core.coord import Coord


class BikeStatus(Enum):
    AVAILABLE = auto()
    IN_USE = auto()
    MAINTENANCE = auto()
    LOST = auto()


@dataclass
class Bike:
    """A single shared bike."""

    bike_id: str
    status: BikeStatus = BikeStatus.AVAILABLE
    station_id: str | None = None  # docked station (None when in use / lost)
    position: Coord | None = None
    total_rides: int = 0
    total_distance_km: float = 0.0
    battery_level: float = 100.0  # for e-bikes

    def dock(self, station_id: str) -> None:
        """Dock the bike at *station_id*."""
        self.station_id = station_id
        self.status = BikeStatus.AVAILABLE

    def undock(self) -> None:
        """Undock the bike for a trip."""
        self.station_id = None
        self.status = BikeStatus.IN_USE


@dataclass
class Fleet:
    """Mutable fleet state — tracks all bikes and their docking positions."""

    bikes: dict[str, Bike] = field(default_factory=dict)

    def add_bike(self, bike: Bike) -> None:
        self.bikes[bike.bike_id] = bike

    def remove_bike(self, bike_id: str) -> Bike | None:
        return self.bikes.pop(bike_id, None)

    def get_bike(self, bike_id: str) -> Bike | None:
        return self.bikes.get(bike_id)

    def bikes_at_station(self, station_id: str) -> list[Bike]:
        return [b for b in self.bikes.values() if b.station_id == station_id]

    def relocate_bikes(
        self,
        from_station: str,
        to_station: str,
        count: int,
        valid_stations: set[str] | None = None,
    ) -> int:
        """Move *count* available bikes from *from_station* to *to_station*.

        Args:
            from_station: Source station ID.
            to_station: Destination station ID.
            count: Maximum number of bikes to move.
            valid_stations: Optional set of valid station IDs. When provided,
                both *from_station* and *to_station* are validated against it,
                and a ``ValueError`` is raised if either is not found.

        Returns:
            The number of bikes actually moved (may be less than *count*
            if there aren't enough available bikes at the source station).

        Raises:
            ValueError: If *valid_stations* is provided and *from_station* or
                *to_station* is not in the set.
        """
        if valid_stations is not None:
            if from_station not in valid_stations:
                raise ValueError(
                    f"Unknown from_station: '{from_station}'. "
                    f"Valid stations: {sorted(valid_stations)}"
                )
            if to_station not in valid_stations:
                raise ValueError(
                    f"Unknown to_station: '{to_station}'. "
                    f"Valid stations: {sorted(valid_stations)}"
                )

        moved = 0
        for bike in self.bikes.values():
            if bike.station_id == from_station and bike.status == BikeStatus.AVAILABLE:
                bike.station_id = to_station
                moved += 1
                if moved >= count:
                    break
        return moved

    def snapshot(self) -> FleetSnapshot:
        """Return an immutable snapshot of the current fleet state."""
        return FleetSnapshot(
            bikes=tuple(self.bikes.values()),
            total=self._count_by_status(),
        )

    def _count_by_status(self) -> dict[str, int]:
        counts: dict[str, int] = {s.name: 0 for s in BikeStatus}
        for b in self.bikes.values():
            counts[b.status.name] += 1
        return counts


@dataclass(frozen=True)
class FleetSnapshot:
    """Immutable point-in-time view of fleet state (safe for API consumption)."""

    bikes: tuple[Bike, ...]
    total: dict[str, int]

    @property
    def total_bikes(self) -> int:
        return len(self.bikes)
