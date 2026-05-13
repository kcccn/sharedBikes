"""Rebalancing scheduler — decides when and where to move bikes.

Phase D (v0.4): Adds ``DispatchCost`` dataclass and
``CostAwareRebalanceStrategy`` — a strategy that scores dispatch
orders by (benefit - cost) and respects a daily budget constraint.

Architecture invariant: ``RebalanceStrategy.analyse()`` signature is
locked. New strategies receive static/ambient data via constructor
injection, not by modifying the abstract interface.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from app.core.fleet import Fleet


# ── dispatch cost model ─────────────────────────────────────────


@dataclass(frozen=True)
class DispatchCost:
    """Cost parameters for a single rebalancing dispatch operation.

    Used by ``CostAwareRebalanceStrategy`` to score candidate orders::

        total_cost = fixed_cost + distance * per_km_cost + n_bikes * per_bike_cost
    """

    fixed_cost: float = 10.0       # per dispatch truck trip
    per_km_cost: float = 2.0       # per unit distance (km along road network)
    per_bike_cost: float = 0.5     # per bike loaded/unloaded

    def total(self, distance_km: float, n_bikes: int) -> float:
        """Compute total cost for a dispatch order."""
        return self.fixed_cost + distance_km * self.per_km_cost + n_bikes * self.per_bike_cost


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


# ── Phase D: cost-aware rebalancing ─────────────────────────────


class CostAwareRebalanceStrategy(RebalanceStrategy):
    """Dispatch orders scored by (benefit - cost), respecting budget.

    Constructor injection (not ``analyse()`` signature change)::

        strategy = CostAwareRebalanceStrategy(
            distance_fn=city.shortest_path_distance,
            station_positions=station_positions,  # station_id → Coord
            budget=1000.0,
        )

    Benefit is measured as starvation-risk reduction: how "saved" a
    starving station would be by receiving *n* bikes. Cost is computed
    via ``DispatchCost`` including distance, fixed truck cost, and
    per-bike handling.
    """

    def __init__(
        self,
        distance_fn: Callable[[str, str], float | None],
        station_positions: dict[str, object] | None = None,
        budget: float = 1000.0,
        dispatch_cost: DispatchCost | None = None,
        benefit_per_bike: float = 5.0,
        max_orders_per_tick: int = 5,
    ) -> None:
        """Initialise the cost-aware strategy.

        Args:
            distance_fn: Callable[str, str] -> float | None, used to get
                road-network distance between two station IDs. Typically
                ``City.shortest_path_distance``.
            station_positions: Optional mapping of station_id → position
                objects. Used for diagnostics only (distance is computed
                via ``distance_fn``).
            budget: Daily dispatch budget. Total dispatch cost per tick
                is limited by remaining budget.
            dispatch_cost: Cost parameters. Uses defaults if not specified.
            benefit_per_bike: How much "benefit" (in currency units) each
                bike delivered to a starving station provides.
            max_orders_per_tick: Maximum number of dispatch orders to
                generate per tick.
        """
        self._distance_fn = distance_fn
        self._station_positions = station_positions or {}
        self._budget = budget
        self._dispatch_cost = dispatch_cost or DispatchCost()
        self._benefit_per_bike = benefit_per_bike
        self._max_orders_per_tick = max_orders_per_tick
        self._budget_spent: float = 0.0

    @property
    def budget_remaining(self) -> float:
        """Remaining dispatch budget."""
        return max(0.0, self._budget - self._budget_spent)

    def reset_budget(self) -> None:
        """Reset the daily budget counter (call at day boundary)."""
        self._budget_spent = 0.0

    def set_budget(self, budget: float) -> None:
        """Update the daily budget (for dynamic adjustments)."""
        self._budget = budget

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

        if not starving or not overflowing:
            return FleetBalanceReport(
                starving_stations=starving,
                overflowing_stations=overflowing,
                healthy_stations=healthy,
            )

        # Score candidate orders by net benefit
        candidates: list[tuple[float, str, str, int]] = []

        for oid in overflowing:
            inv = station_inventory.get(oid, 0)
            cap = station_capacity.get(oid, 1)
            # How many bikes can we take from this overflowing station?
            excess = inv - int(cap * threshold_high)
            if excess <= 0:
                continue

            for sid in starving:
                distance = self._distance_fn(oid, sid)
                if distance is None:
                    distance = 2.0  # fallback

                # How many bikes does the starving station need?
                need = int(cap * threshold_low) - station_inventory.get(sid, 0)
                if need <= 0:
                    continue

                n_bikes = min(excess, need, 3)  # max 3 per order

                cost = self._dispatch_cost.total(distance, n_bikes)
                benefit = n_bikes * self._benefit_per_bike
                net_benefit = benefit - cost

                candidates.append((net_benefit, oid, sid, n_bikes))

        # Sort by net benefit descending
        candidates.sort(key=lambda x: x[0], reverse=True)

        orders: list[DispatchOrder] = []
        order_id = 0
        remaining = self.budget_remaining

        for net_benefit, oid, sid, n_bikes in candidates:
            if order_id >= self._max_orders_per_tick:
                break

            distance = self._distance_fn(oid, sid) or 2.0
            cost = self._dispatch_cost.total(distance, n_bikes)

            # Skip if this order would exceed budget
            if cost > remaining:
                continue

            # Only dispatch if net benefit is positive
            if net_benefit <= 0:
                continue

            orders.append(
                DispatchOrder(
                    order_id=f"cost-aware-order-{order_id}",
                    from_station=oid,
                    to_station=sid,
                    count=n_bikes,
                    priority=int(net_benefit),
                )
            )
            self._budget_spent += cost
            remaining -= cost
            order_id += 1

        return FleetBalanceReport(
            starving_stations=starving,
            overflowing_stations=overflowing,
            healthy_stations=healthy,
            suggested_orders=orders,
        )
