"""Rebalancing scheduler — fleet redistribution strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class DispatchOrder:
    """An instruction to move bikes between stations."""

    vehicle_id: str
    from_station: str
    to_station: str
    bike_count: int
    estimated_minutes: float


@dataclass
class FleetBalanceReport:
    """Identifies stations that are over/under-supplied."""

    starving: list[str]          # stations below min threshold
    overflowing: list[str]       # stations above max threshold
    suggested_orders: list[DispatchOrder] = field(default_factory=list)


class RebalanceStrategy(ABC):
    """Strategy pattern — different algorithms for different fleet scales."""

    @abstractmethod
    def analyse(
        self,
        station_inventory: dict[str, list[str]],
        station_capacity: dict[str, int],
    ) -> FleetBalanceReport:
        ...


class GreedyThresholdStrategy(RebalanceStrategy):
    """Simple threshold-based strategy: if <20% or >80% full, flag it."""

    def __init__(self, low_ratio: float = 0.2, high_ratio: float = 0.8):
        self.low_ratio = low_ratio
        self.high_ratio = high_ratio

    def analyse(
        self,
        station_inventory: dict[str, list[str]],
        station_capacity: dict[str, int],
    ) -> FleetBalanceReport:
        starving: list[str] = []
        overflowing: list[str] = []

        for sid, capacity in station_capacity.items():
            if capacity <= 0:
                continue  # skip closed / zero-capacity stations
            count = len(station_inventory.get(sid, []))
            ratio = count / capacity
            if ratio < self.low_ratio:
                starving.append(sid)
            elif ratio > self.high_ratio:
                overflowing.append(sid)

        return FleetBalanceReport(
            starving=starving,
            overflowing=overflowing,
        )
