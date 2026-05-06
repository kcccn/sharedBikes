"""Rebalancing strategy pattern."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.core.city import Station
from app.core.fleet import FleetSnapshot


@dataclass
class DispatchOrder:
    """A single rebalancing instruction."""

    from_station_id: str
    to_station_id: str
    bike_count: int
    reason: str = ""


@dataclass
class FleetBalanceReport:
    """Output of a rebalancing analysis."""

    starving_stations: list[tuple[Station, int]]  # station, deficit
    overflowing_stations: list[tuple[Station, int]]  # station, excess
    suggested_orders: list[DispatchOrder] = field(default_factory=list)


class RebalanceStrategy(ABC):
    """Interface for rebalancing algorithms."""

    @abstractmethod
    def analyse(
        self,
        stations: tuple[Station, ...],
        snapshot: FleetSnapshot,
    ) -> FleetBalanceReport:
        ...


class GreedyThresholdStrategy(RebalanceStrategy):
    """Simple greedy rebalancer: threshold-based pairing."""

    def __init__(self, low_threshold: float = 0.2, high_threshold: float = 0.8):
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold

    def analyse(
        self,
        stations: tuple[Station, ...],
        snapshot: FleetSnapshot,
    ) -> FleetBalanceReport:
        starving: list[tuple[Station, int]] = []
        overflowing: list[tuple[Station, int]] = []

        for station in stations:
            current = snapshot.station_inventory.get(station.station_id, 0)
            if station.capacity == 0:
                continue
            ratio = current / station.capacity
            if ratio <= self.low_threshold:
                deficit = math.ceil(station.capacity * self.low_threshold) - current
                if deficit > 0:
                    starving.append((station, deficit))
            elif ratio >= self.high_threshold:
                excess = current - math.floor(station.capacity * self.high_threshold)
                if excess > 0:
                    overflowing.append((station, excess))

        orders: list[DispatchOrder] = []
        for s_station, deficit in starving:
            for o_station, excess in overflowing:
                if deficit <= 0:
                    break
                move = min(deficit, excess)
                orders.append(
                    DispatchOrder(
                        from_station_id=o_station.station_id,
                        to_station_id=s_station.station_id,
                        bike_count=move,
                        reason=f"greedy: {o_station.name}→{s_station.name}",
                    )
                )
                deficit -= move

        return FleetBalanceReport(
            starving_stations=starving,
            overflowing_stations=overflowing,
            suggested_orders=orders,
        )
