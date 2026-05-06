"""Scheduler — rebalancing strategies to redistribute bikes across stations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import NamedTuple


class DispatchOrder(NamedTuple):
    """A single rebalancing instruction: move n bikes between stations."""

    from_station_id: str
    to_station_id: str
    count: int


class FleetBalanceReport(NamedTuple):
    """Summary of fleet balance and suggested rebalancing orders."""

    starving_stations: list[tuple[str, int]]  # station_id, deficit
    overflowing_stations: list[tuple[str, int]]  # station_id, surplus
    suggested_orders: list[DispatchOrder]


class RebalanceStrategy(ABC):
    """Pluggable strategy for computing rebalancing orders."""

    @abstractmethod
    def analyse(
        self,
        inventory: dict[str, int],
        capacities: dict[str, int],
    ) -> FleetBalanceReport:
        ...


@dataclass
class GreedyThresholdStrategy(RebalanceStrategy):
    """Simple greedy strategy: pair starving ↔ overflowing stations if the
    imbalance exceeds configurable thresholds."""

    low_threshold: float = 0.2  # fraction of capacity → starving
    high_threshold: float = 0.8  # fraction of capacity → overflowing

    def analyse(
        self,
        inventory: dict[str, int],
        capacities: dict[str, int],
    ) -> FleetBalanceReport:
        starving: list[tuple[str, int]] = []
        overflowing: list[tuple[str, int]] = []

        for sid in inventory:
            cap = capacities.get(sid, 30)
            if cap <= 0:
                continue  # skip zero-capacity or removed stations
            occupancy = inventory[sid] / cap
            deficit = max(0, int(cap * self.low_threshold) - inventory[sid])
            surplus = max(0, inventory[sid] - int(cap * self.high_threshold))
            if deficit > 0:
                starving.append((sid, deficit))
            if surplus > 0:
                overflowing.append((sid, surplus))

        # Simple greedy pairing
        orders: list[DispatchOrder] = []
        i, j = 0, 0
        while i < len(starving) and j < len(overflowing):
            sid_starve, need = starving[i]
            sid_over, have = overflowing[j]
            move = min(need, have)
            if move > 0:
                orders.append(DispatchOrder(sid_over, sid_starve, move))
            starving[i] = (sid_starve, need - move)
            overflowing[j] = (sid_over, have - move)
            if starving[i][1] <= 0:
                i += 1
            if overflowing[j][1] <= 0:
                j += 1

        return FleetBalanceReport(
            starving_stations=starving[i:],
            overflowing_stations=overflowing[j:],
            suggested_orders=orders,
        )
