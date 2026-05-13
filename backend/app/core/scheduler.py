"""Rebalancing scheduler — decides when and where to move bikes."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.coord import Coord
    from app.core.dispatch_cost import DispatchBudget, DispatchCostParams
    from app.core.fleet import Fleet


@dataclass(frozen=True)
class DispatchOrder:
    """A single rebalancing instruction."""

    order_id: str
    from_station: str
    to_station: str
    count: int
    priority: int = 0  # higher = more urgent


@dataclass(frozen=True)
class FleetBalanceReport:
    """Snapshot of current fleet balance state with suggestions."""

    starving_stations: list[str] = field(default_factory=list)
    overflowing_stations: list[str] = field(default_factory=list)
    healthy_stations: list[str] = field(default_factory=list)
    suggested_orders: list[DispatchOrder] = field(default_factory=list)


class RebalanceStrategy(ABC):
    """Pluggable strategy for generating rebalance orders."""

    @abstractmethod
    def analyse(
        self,
        station_inventory: dict[str, int],
        station_capacity: dict[str, int],
        threshold_low: float = 0.2,
        threshold_high: float = 0.8,
    ) -> FleetBalanceReport:
        ...

    def apply_orders(
        self,
        orders: list[DispatchOrder],
        fleet: Fleet,
        valid_stations: set[str] | None = None,
    ) -> list[tuple[str, str, int]]:
        """Execute dispatch orders against the fleet.

        Args:
            orders: List of dispatch orders to execute.
            fleet: The fleet to execute orders against.
            valid_stations: Optional set of valid station IDs. Passed through
                to ``Fleet.relocate_bikes()`` for validation.

        Returns:
            List of (from_station, to_station, actual_count) tuples
            representing successfully executed movements.
        """
        executed: list[tuple[str, str, int]] = []
        for order in orders:
            moved = fleet.relocate_bikes(
                order.from_station,
                order.to_station,
                order.count,
                valid_stations=valid_stations,
            )
            if moved > 0:
                executed.append((order.from_station, order.to_station, moved))
        return executed


class GreedyThresholdStrategy(RebalanceStrategy):
    """Simple greedy: pair starving ↔ overflowing stations."""

    def analyse(
        self,
        station_inventory: dict[str, int],
        station_capacity: dict[str, int],
        threshold_low: float = 0.2,
        threshold_high: float = 0.8,
    ) -> FleetBalanceReport:
        starving: list[str] = []
        overflowing: list[str] = []
        healthy: list[str] = []

        for sid, cap in station_capacity.items():
            if cap <= 0:
                healthy.append(sid)
                continue
            inv = station_inventory.get(sid, 0)
            ratio = inv / cap
            if ratio < threshold_low:
                starving.append(sid)
            elif ratio > threshold_high:
                overflowing.append(sid)
            else:
                healthy.append(sid)

        orders: list[DispatchOrder] = []
        order_id = 0
        for oid in overflowing:
            for sid in starving:
                if order_id >= 10:
                    break
                orders.append(
                    DispatchOrder(
                        order_id=f"order-{order_id}",
                        from_station=oid,
                        to_station=sid,
                        count=1,
                    )
                )
                order_id += 1

        return FleetBalanceReport(
            starving_stations=starving,
            overflowing_stations=overflowing,
            healthy_stations=healthy,
            suggested_orders=orders,
        )


class CostAwareRebalanceStrategy(RebalanceStrategy):
    """Cost-aware rebalancing — only dispatch when benefit exceeds cost.

    Phase D (v0.4): Each dispatch order is scored by (benefit - cost).
    Only cost-effective dispatches are executed. Total dispatches per tick
    are limited by the remaining daily budget.
    """

    def __init__(
        self,
        cost_params=None,
        budget=None,
        cost_benefit_ratio: float = 1.5,
        max_orders_per_tick: int = 5,
        base_value_per_bike: float = 15.0,
    ) -> None:
        from app.core.dispatch_cost import DEFAULT_DISPATCH_COST, DispatchBudget

        self.cost_params = cost_params or DEFAULT_DISPATCH_COST
        self.budget = budget or DispatchBudget()
        self.cost_benefit_ratio = cost_benefit_ratio
        self.max_orders_per_tick = max_orders_per_tick
        self.base_value_per_bike = base_value_per_bike
        self._station_positions: dict = {}

    def set_station_positions(self, positions: dict) -> None:
        """Set station positions for distance-aware cost calculation."""
        self._station_positions = positions

    def _distance_between(self, from_id: str, to_id: str) -> float:
        """Return distance in km between two stations."""
        a = self._station_positions.get(from_id)
        b = self._station_positions.get(to_id)
        if a is None or b is None:
            return 2.0
        return a.distance_to(b)

    def analyse(
        self,
        station_inventory: dict[str, int],
        station_capacity: dict[str, int],
        threshold_low: float = 0.2,
        threshold_high: float = 0.8,
    ) -> FleetBalanceReport:
        from app.core.dispatch_cost import calculate_dispatch_cost, estimate_benefit

        starving: list[str] = []
        overflowing: list[str] = []
        healthy: list[str] = []

        for sid, cap in station_capacity.items():
            if cap <= 0:
                healthy.append(sid)
                continue
            inv = station_inventory.get(sid, 0)
            ratio = inv / cap
            if ratio < threshold_low:
                starving.append(sid)
            elif ratio > threshold_high:
                overflowing.append(sid)
            else:
                healthy.append(sid)

        scored_orders: list[tuple[float, str, str, int]] = []

        for oid in overflowing:
            cap = station_capacity.get(oid, 0)
            inv = station_inventory.get(oid, 0)
            available = max(1, int(inv - cap * threshold_high))

            for sid in starving:
                cap_s = station_capacity.get(sid, 0)
                inv_s = station_inventory.get(sid, 0)
                needed = max(1, int(cap_s * threshold_low - inv_s))
                n_bikes = min(available, needed, 3)
                if n_bikes <= 0:
                    continue

                dist = self._distance_between(oid, sid)
                cost = calculate_dispatch_cost(dist, n_bikes, self.cost_params)
                starvation_risk = max(0.0, 1.0 - inv_s / (cap_s * threshold_low)) if cap_s > 0 else 1.0
                starvation_risk = min(1.0, starvation_risk)
                benefit = estimate_benefit(starvation_risk, n_bikes, self.base_value_per_bike)

                if benefit > cost * self.cost_benefit_ratio:
                    score = benefit - cost
                    scored_orders.append((score, oid, sid, n_bikes))

        scored_orders.sort(key=lambda x: x[0], reverse=True)

        orders: list[DispatchOrder] = []
        remaining_budget = self.budget.remaining

        for i, (score, oid, sid, n_bikes) in enumerate(scored_orders):
            if i >= self.max_orders_per_tick:
                break
            dist = self._distance_between(oid, sid)
            order_cost = calculate_dispatch_cost(dist, n_bikes, self.cost_params)
            if order_cost > remaining_budget:
                continue
            remaining_budget -= order_cost
            orders.append(
                DispatchOrder(
                    order_id=f"cost-order-{i}",
                    from_station=oid,
                    to_station=sid,
                    count=n_bikes,
                    priority=int(score),
                )
            )

        return FleetBalanceReport(
            starving_stations=starving,
            overflowing_stations=overflowing,
            healthy_stations=healthy,
            suggested_orders=orders,
        )
