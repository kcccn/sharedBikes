"""Fleet model — bike lifecycle, station inventory, and state snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import NamedTuple


class BikeState(Enum):
    DOCKED = auto()
    IN_TRANSIT = auto()  # being ridden
    BEING_REBALANCED = auto()  # on a truck
    LOST = auto()
    DAMAGED = auto()


@dataclass(frozen=True)
class Bike:
    """A single bike with identity and lifecycle state."""

    bike_id: str
    state: BikeState = BikeState.DOCKED
    current_station_id: str | None = None
    current_trip_id: str | None = None


class FleetSnapshot(NamedTuple):
    """Immutable point-in-time view of the entire fleet."""

    bikes: dict[str, Bike]
    station_inventory: dict[str, int]  # station_id → docked count
    total_bikes: int
    docked_bikes: int
    in_transit_bikes: int
    lost_or_damaged_bikes: int


class BikeNotFoundError(KeyError):
    """Raised when a bike_id does not exist in the fleet."""


class BikeNotDockedError(ValueError):
    """Raised when trying to undock a bike that is not currently docked."""


class StationFullError(ValueError):
    """Raised when trying to dock at a station that has reached capacity."""


@dataclass
class Fleet:
    """Mutable fleet state — mutated each tick by the simulation engine."""

    bikes: dict[str, Bike] = field(default_factory=dict)
    station_inventory: dict[str, int] = field(default_factory=dict)
    _station_capacity: dict[str, int] = field(default_factory=dict)

    # ── lifecycle ────────────────────────────────────────────────────

    def add_bike(self, bike: Bike, station_id: str) -> None:
        """Add a new bike and dock it at the given station."""
        self.bikes[bike.bike_id] = bike
        self._dock_bike_at(bike.bike_id, station_id)

    def dock_bike(self, bike_id: str, station_id: str) -> None:
        """Return a bike to a station (idempotent: undocks first if needed)."""
        if bike_id not in self.bikes:
            raise BikeNotFoundError(bike_id)

        # Undock from previous station if docked
        if self.bikes[bike_id].state == BikeState.DOCKED:
            prev = self.bikes[bike_id].current_station_id
            if prev and prev != station_id:
                self._undock_bike_from(bike_id, prev)

        self._dock_bike_at(bike_id, station_id)

    def undock_bike(self, bike_id: str) -> str:
        """Remove a bike from its station. Returns the former station_id."""
        if bike_id not in self.bikes:
            raise BikeNotFoundError(bike_id)
        bike = self.bikes[bike_id]
        if bike.state != BikeState.DOCKED:
            raise BikeNotDockedError(
                f"Bike {bike_id} is {bike.state.name}, not DOCKED"
            )
        station_id = bike.current_station_id
        if station_id is None:
            raise BikeNotDockedError(f"Bike {bike_id} has no current station")
        self._undock_bike_from(bike_id, station_id)
        return station_id

    def mark_lost(self, bike_id: str) -> None:
        self._set_state(bike_id, BikeState.LOST)

    def mark_damaged(self, bike_id: str) -> None:
        self._set_state(bike_id, BikeState.DAMAGED)

    # ── snapshot ─────────────────────────────────────────────────────

    def snapshot(self) -> FleetSnapshot:
        """Return an immutable point-in-time view."""
        docked = sum(1 for b in self.bikes.values() if b.state == BikeState.DOCKED)
        transit = sum(1 for b in self.bikes.values() if b.state == BikeState.IN_TRANSIT)
        lost = sum(
            1
            for b in self.bikes.values()
            if b.state in (BikeState.LOST, BikeState.DAMAGED)
        )
        return FleetSnapshot(
            bikes=dict(self.bikes),
            station_inventory=dict(self.station_inventory),
            total_bikes=len(self.bikes),
            docked_bikes=docked,
            in_transit_bikes=transit,
            lost_or_damaged_bikes=lost,
        )

    # ── internal helpers ─────────────────────────────────────────────

    def _dock_bike_at(self, bike_id: str, station_id: str) -> None:
        cap = self._station_capacity.get(station_id, 30)
        current = self.station_inventory.get(station_id, 0)
        if current >= cap:
            raise StationFullError(
                f"Station {station_id} at capacity ({cap})"
            )
        self.station_inventory[station_id] = current + 1
        self.bikes[bike_id] = Bike(
            bike_id=bike_id,
            state=BikeState.DOCKED,
            current_station_id=station_id,
            current_trip_id=None,
        )

    def _undock_bike_from(self, bike_id: str, station_id: str) -> None:
        self.station_inventory[station_id] = (
            self.station_inventory.get(station_id, 0) - 1
        )

    def _set_state(self, bike_id: str, state: BikeState) -> None:
        if bike_id not in self.bikes:
            raise BikeNotFoundError(bike_id)
        bike = self.bikes[bike_id]
        self.bikes[bike_id] = Bike(
            bike_id=bike_id,
            state=state,
            current_station_id=bike.current_station_id,
            current_trip_id=bike.current_trip_id,
        )
