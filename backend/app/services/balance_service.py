"""Balance service — orchestrates rebalancing analysis and dispatch."""

from app.core.fleet import Fleet
from app.core.scheduler import FleetBalanceReport, RebalanceStrategy


class BalanceService:
    """Coordinates rebalancing analysis between fleet and strategy."""

    def __init__(self, strategy: RebalanceStrategy) -> None:
        self._strategy = strategy

    def analyse(
        self,
        fleet: Fleet,
        station_capacity: dict[str, int],
        threshold_low: float = 0.2,
        threshold_high: float = 0.8,
    ) -> FleetBalanceReport:
        """Run the rebalancing strategy and return a balance report.
        
        Args:
            fleet: Current fleet state.
            station_capacity: Mapping of station_id → capacity.
            threshold_low: Ratio below which a station is considered starving.
            threshold_high: Ratio above which a station is considered overflowing.
        """
        station_inventory: dict[str, int] = {}
        for sid in station_capacity:
            station_inventory[sid] = len(fleet.bikes_at_station(sid))

        return self._strategy.analyse(
            station_inventory,
            station_capacity,
            threshold_low=threshold_low,
            threshold_high=threshold_high,
        )
