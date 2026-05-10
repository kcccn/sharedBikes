"""Rebalancing scheduler — decides when and where to move bikes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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
