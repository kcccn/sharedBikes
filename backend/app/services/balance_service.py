"""Balance service — executes rebalance dispatch orders."""

from __future__ import annotations

from app.core.fleet import Fleet
from app.core.scheduler import DispatchOrder


class BalanceService:
    """Executes dispatch orders (truck routing, batch moves).

    Phase 3 goal: implement truck fleet management with:
    - Multi-stop route optimisation (genetic algorithm / OR-Tools)
    - Driver shift scheduling
    - Cost tracking per dispatch
    """

    async def dispatch(self, fleet: Fleet, order: DispatchOrder) -> bool:
        """Execute a single dispatch order.

        Returns ``True`` if the order was fully executed.
        """
        _ = fleet, order
        raise NotImplementedError("Phase 3: implement dispatch execution")
