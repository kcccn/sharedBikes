"""Balance service — orchestrates rebalancing analysis and dispatch."""

from app.core.fleet import Fleet
from app.core.scheduler import FleetBalanceReport, RebalanceStrategy


class BalanceService:
    """Coordinates rebalancing analysis between fleet and strategy."""

    def __init__(self, strategy: RebalanceStrategy) -> None:
        self._strategy = strategy

    def analyse(self, fleet: Fleet) -> FleetBalanceReport:
        station_capacity: dict[str, int] = {}
        inventory = fleet.inventory
        # capacity info is stored externally — this is a stub
        return self._strategy.analyse(inventory, station_capacity)
