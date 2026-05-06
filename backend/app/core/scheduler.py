"""Rebalancing scheduler — strategy pattern for fleet balancing."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class DispatchOrder:
    """A single rebalancing instruction."""

    from_station_id: str
    to_station_id: str
    bike_count: int
    truck_id: str | None = None


@dataclass
class FleetBalanceReport:
    """Snapshot of the fleet balance analysis."""

    starving_stations: list[str] = field(default_factory=list)
    overflowing_stations: list[str] = field(default_factory=list)
    suggested_orders: list[DispatchOrder] = field(default_factory=list)


class RebalanceStrategy(ABC):
    """Pluggable strategy for analysing fleet balance."""

    @abstractmethod
    def analyse(
        self,
        station_inventory: dict[str, list[str]],
        station_capacity: dict[str, int],
    ) -> FleetBalanceReport:
        """Analyse inventory and capacity, return a balance report."""


class GreedyThresholdStrategy(RebalanceStrategy):
    """Simple threshold-based strategy — stations below *low* or above *high*."""

    def __init__(self, low_ratio: float = 0.2, high_ratio: float = 0.8) -> None:
        self.low_ratio = low_ratio
        self.high_ratio = high_ratio

    def analyse(
        self,
        station_inventory: dict[str, list[str]],
        station_capacity: dict[str, int],
    ) -> FleetBalanceReport:
        starving: list[str] = []
        overflowing: list[str] = []
        for sid, cap in station_capacity.items():
            if cap <= 0:
                continue  # skip stations with no capacity
            count = len(station_inventory.get(sid, []))
            ratio = count / cap
            if ratio < self.low_ratio:
                starving.append(sid)
            elif ratio > self.high_ratio:
                overflowing.append(sid)
        return FleetBalanceReport(
            starving_stations=starving,
            overflowing_stations=overflowing,
        )
