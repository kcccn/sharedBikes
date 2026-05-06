"""Rebalancing scheduler — strategy pattern for fleet redistribution."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DispatchOrder:
    """A single rebalancing instruction."""

    truck_id: str
    from_station: str
    to_station: str
    bike_count: int
    priority: int  # higher = more urgent


@dataclass(frozen=True)
class StationBalance:
    """Balance status of a single station."""

    station_id: str
    current_bikes: int
    capacity: int
    utilization: float  # 0.0 – 1.0
    is_starving: bool
    is_overflowing: bool


@dataclass(frozen=True)
class FleetBalanceReport:
    """Snapshot of balance across all stations."""

    stations: dict[str, StationBalance]
    suggested_orders: list[DispatchOrder] = field(default_factory=list)


class RebalanceStrategy(ABC):
    """Abstract rebalancing strategy."""

    @abstractmethod
    def analyse(
        self,
        station_counts: dict[str, int],
        station_capacities: dict[str, int],
        starvation_threshold: float,
        overflow_threshold: float,
    ) -> FleetBalanceReport:
        ...


class GreedyThresholdStrategy(RebalanceStrategy):
    """Simple greedy strategy: pair starving ↔ overflowing stations."""

    def analyse(
        self,
        station_counts: dict[str, int],
        station_capacities: dict[str, int],
        starvation_threshold: float,
        overflow_threshold: float,
    ) -> FleetBalanceReport:
        stations: dict[str, StationBalance] = {}
        starving: list[tuple[str, int]] = []  # (station_id, deficit)
        overflowing: list[tuple[str, int]] = []  # (station_id, surplus)

        for sid, capacity in station_capacities.items():
            if capacity <= 0:
                continue
            count = station_counts.get(sid, 0)
            util = count / capacity
            is_starving = util < starvation_threshold
            is_overflowing = util > overflow_threshold

            stations[sid] = StationBalance(
                station_id=sid,
                current_bikes=count,
                capacity=capacity,
                utilization=round(util, 3),
                is_starving=is_starving,
                is_overflowing=is_overflowing,
            )

            if is_starving:
                deficit = max(0, int(capacity * starvation_threshold) - count)
                starving.append((sid, deficit))
            if is_overflowing:
                surplus = max(0, count - int(capacity * overflow_threshold))
                overflowing.append((sid, surplus))

        # Greedy match: overflowing → starving
        orders: list[DispatchOrder] = []
        truck_id = "truck-01"
        priority = 1

        for osid, surplus in sorted(overflowing, key=lambda x: -x[1]):
            remaining = surplus
            for ssid, deficit in sorted(starving, key=lambda x: -x[1]):
                if remaining <= 0:
                    break
                if deficit <= 0:
                    continue
                move = min(remaining, deficit)
                orders.append(
                    DispatchOrder(
                        truck_id=truck_id,
                        from_station=osid,
                        to_station=ssid,
                        bike_count=move,
                        priority=priority,
                    )
                )
                remaining -= move
                # Update deficit in starving list (in‑place)
                starving = [
                    (sid, d - move if sid == ssid else d)
                    for sid, d in starving
                ]
            priority += 1

        return FleetBalanceReport(stations=stations, suggested_orders=orders)
