"""Fleet balance & rebalancing service."""

from __future__ import annotations

from typing import Any

from app.core.fleet import FleetSnapshot
from app.core.scheduler import FleetBalanceReport, GreedyThresholdStrategy


class BalanceService:
    """Orchestrates fleet rebalancing analysis."""

    def __init__(self) -> None:
        self.strategy = GreedyThresholdStrategy()

    def analyse(
        self,
        fleet_snapshot: FleetSnapshot,
        capacities: dict[str, int],
        starvation_threshold: float = 0.2,
        overflow_threshold: float = 0.8,
    ) -> FleetBalanceReport:
        return self.strategy.analyse(
            station_counts=fleet_snapshot.station_counts,
            station_capacities=capacities,
            starvation_threshold=starvation_threshold,
            overflow_threshold=overflow_threshold,
        )
