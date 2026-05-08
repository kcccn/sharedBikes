"""Cost engine — pure functions for fixed/variable cost calculation.

Each tick, the cost engine computes costs that should be deducted
from the ledger. Costs are negative amounts in ``LedgerEntry``.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.finance import CostCategory, LedgerEntry


@dataclass(frozen=True)
class CostParams:
    """Tunable cost parameters — modifiable via TOML in future."""

    maintenance_per_bike_per_day: float = 0.5
    lease_per_station_per_day: float = 10.0
    overhead_per_tick: float = 0.0


DEFAULT_COST_PARAMS = CostParams()


class CostEngine:
    """Pure-function cost engine — stateless, no side effects.

    Costs are computed at the end of each tick and posted to the ledger
    as negative ``LedgerEntry`` amounts.
    """

    def __init__(self, params: CostParams = DEFAULT_COST_PARAMS) -> None:
        self._params = params

    def per_tick(
        self,
        tick: int,
        tick_in_day: int,
        total_bikes: int,
        total_stations: int,
    ) -> list[LedgerEntry]:
        """Compute costs for a single tick.

        Returns a list of ``LedgerEntry`` with negative amounts.
        Fixed costs (lease, maintenance) are posted only on the first
        tick of each day (tick_in_day == 0).
        """
        entries: list[LedgerEntry] = []

        # Daily fixed costs — posted once per day at tick 0
        if tick_in_day == 0:
            day = tick // 1440

            maintenance = self._params.maintenance_per_bike_per_day * total_bikes
            if maintenance > 0:
                entries.append(LedgerEntry(
                    tick=tick,
                    entry_id=f"cost-maint-{tick}",
                    category=CostCategory.BIKE_MAINTENANCE,
                    amount=-round(maintenance, 2),
                    description=f"day {day}: maintenance for {total_bikes} bikes @ ¥{self._params.maintenance_per_bike_per_day}/ea",
                ))

            lease = self._params.lease_per_station_per_day * total_stations
            if lease > 0:
                entries.append(LedgerEntry(
                    tick=tick,
                    entry_id=f"cost-lease-{tick}",
                    category=CostCategory.STATION_LEASE,
                    amount=-round(lease, 2),
                    description=f"day {day}: lease for {total_stations} stations @ ¥{self._params.lease_per_station_per_day}/ea",
                ))

        # Per-tick overhead
        if self._params.overhead_per_tick > 0:
            entries.append(LedgerEntry(
                tick=tick,
                entry_id=f"cost-overhead-{tick}",
                category=CostCategory.OVERHEAD,
                amount=-round(self._params.overhead_per_tick, 4),
                description="per-tick overhead",
            ))

        return entries
