"""Rebalancing strategies for fleet redistribution."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.core.city import City, Station
from app.core.fleet import FleetSnapshot


@dataclass
class DispatchOrder:
    """A single rebalance instruction: move N bikes between stations."""

    from_station_id: str
    to_station_id: str
    bike_count: int


@dataclass
class FleetBalanceReport:
    """Outcome of a rebalance analysis."""

    starving_stations: list[Station] = field(default_factory=list)
    overflowing_stations: list[Station] = field(default_factory=list)
    suggested_orders: list[DispatchOrder] = field(default_factory=list)


class RebalanceStrategy(ABC):
    """Pluggable strategy for detecting and correcting fleet imbalance."""

    @abstractmethod
    def analyse(
        self,
        city: City,
        snapshot: FleetSnapshot,
        tick: int,
    ) -> FleetBalanceReport:
        """Analyse the current fleet state and return balance recommendations."""


class GreedyThresholdStrategy(RebalanceStrategy):
    """A simple greedy strategy: pair starving ↔ overflowing stations.

    A station is *starving* when its fill ratio is below *low_threshold*.
    A station is *overflowing* when its fill ratio is above *high_threshold*.
    """

    def __init__(
        self,
        low_threshold: float = 0.2,
        high_threshold: float = 0.8,
        max_bikes_per_order: int = 5,
    ) -> None:
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.max_bikes_per_order = max_bikes_per_order

    def analyse(
        self,
        city: City,
        snapshot: FleetSnapshot,
        tick: int,
    ) -> FleetBalanceReport:
        _ = tick  # not used in this strategy
        starving: list[Station] = []
        overflowing: list[Station] = []

        for station in city.stations.values():
            if station.capacity <= 0:
                continue  # skip zero-capacity stations
            inventory = snapshot.station_inventory.get(station.id, 0)
            ratio = inventory / station.capacity
            if ratio < self.low_threshold:
                starving.append(station)
            elif ratio > self.high_threshold:
                overflowing.append(station)

        orders: list[DispatchOrder] = []
        for src in overflowing:
            for dst in starving:
                # Pair overflowing → starving with a cap
                transfer = min(
                    self.max_bikes_per_order,
                    snapshot.station_inventory.get(src.id, 0),
                    dst.capacity - snapshot.station_inventory.get(dst.id, 0),
                )
                if transfer > 0:
                    orders.append(DispatchOrder(
                        from_station_id=src.id,
                        to_station_id=dst.id,
                        bike_count=transfer,
                    ))

        return FleetBalanceReport(
            starving_stations=starving,
            overflowing_stations=overflowing,
            suggested_orders=orders,
        )
