"""Rebalancing scheduler — strategy pattern for dispatch logic."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field


@dataclass
class DispatchOrder:
    """A single rebalancing instruction."""

    order_id: str
    from_station: str
    to_station: str
    bike_count: int


@dataclass
class FleetBalanceReport:
    """Report produced by a rebalancing strategy."""

    starving_stations: list[str] = field(default_factory=list)
    overflowing_stations: list[str] = field(default_factory=list)
    suggested_orders: list[DispatchOrder] = field(default_factory=list)


class RebalanceStrategy(abc.ABC):
    """Strategy interface for rebalancing algorithms."""

    @abc.abstractmethod
    def analyse(
        self,
        inventory: dict[str, int],
        station_capacity: dict[str, int],
    ) -> FleetBalanceReport:
        ...


class GreedyThresholdStrategy(RebalanceStrategy):
    """Simple threshold-based strategy: stations below 20% or above 80%."""

    def __init__(self, low_ratio: float = 0.2, high_ratio: float = 0.8) -> None:
        self.low_ratio = low_ratio
        self.high_ratio = high_ratio

    def analyse(
        self,
        inventory: dict[str, int],
        station_capacity: dict[str, int],
    ) -> FleetBalanceReport:
        starving: list[str] = []
        overflowing: list[str] = []
        for sid, cap in station_capacity.items():
            if cap <= 0:
                continue
            current = inventory.get(sid, 0)
            ratio = current / cap
            if ratio < self.low_ratio:
                starving.append(sid)
            elif ratio > self.high_ratio:
                overflowing.append(sid)
        return FleetBalanceReport(
            starving_stations=starving,
            overflowing_stations=overflowing,
        )
