"""
Rebalancing strategies — the brains behind fleet dispatch.

Each strategy implements the Dispatcher protocol and is hot-swappable.
This lets us compare:
  • Greedy: send nearest vehicle to most imbalanced station.
  • Tabu search: avoid short-term cycles in dispatch decisions.
  • Genetic algorithm: optimize multi-vehicle routes over a time horizon.
  • RL agent (future): learned policy from replay data.

The strategy receives the current world state snapshot and produces
a list of RebalanceTrip... events.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..core.models import GeoPoint, RebalanceVehicle, Station


@dataclass
class DispatchOrder:
    """A single instruction: send vehicle to station, pick up/drop off N bikes."""
    vehicle_id: str
    target_station_id: str
    bikes_to_pickup: int
    bikes_to_dropoff: int
    priority: float = 0.0


class Dispatcher(Protocol):
    """Protocol for any rebalancing strategy."""

    def plan(
        self,
        vehicles: list[RebalanceVehicle],
        stations: list[Station],
        bike_density: dict[str, float],       # station_id -> bikes / capacity
        time_horizon_hours: float = 2.0,
    ) -> list[DispatchOrder]:
        ...


# ── Concrete: Greedy Threshold ──────────────────────────────────────

@dataclass
class GreedyThresholdDispatcher:
    """
    Simplest useful strategy:
    - If a station is >80% full, send a vehicle to pick up bikes.
    - If a station is <20% full, send a vehicle to drop off bikes.
    - Assign the closest available vehicle.
    """
    upper_threshold: float = 0.8
    lower_threshold: float = 0.2

    def plan(
        self,
        vehicles: list[RebalanceVehicle],
        stations: list[Station],
        bike_density: dict[str, float],
        time_horizon_hours: float = 2.0,
    ) -> list[DispatchOrder]:
        orders: list[DispatchOrder] = []
        for station in stations:
            density = bike_density.get(station.station_id, 0.5)
            if density > self.upper_threshold:
                # Overflow — need pickup
                orders.append(DispatchOrder(
                    vehicle_id="",
                    target_station_id=station.station_id,
                    bikes_to_pickup=int((density - 0.5) * station.capacity),
                    bikes_to_dropoff=0,
                    priority=density,
                ))
            elif density < self.lower_threshold:
                # Underflow — need dropoff
                orders.append(DispatchOrder(
                    vehicle_id="",
                    target_station_id=station.station_id,
                    bikes_to_pickup=0,
                    bikes_to_dropoff=int((0.5 - density) * station.capacity),
                    priority=1.0 - density,
                ))
        orders.sort(key=lambda o: o.priority, reverse=True)
        return orders
