"""Service stubs — to be implemented in Phase 1."""

from app.core.city import City
from app.core.fleet import FleetSnapshot


class MapService:
    """Load and manage city road network data."""

    async def load_city(self, name: str) -> City:
        raise NotImplementedError("Phase 1")


class DemandService:
    """Generate trip demand based on time and location."""

    async def generate_trips(self, snapshot: FleetSnapshot) -> list[dict]:
        raise NotImplementedError("Phase 1")


class BalanceService:
    """Execute rebalancing orders via dispatch."""

    async def dispatch_orders(self, orders: list) -> None:
        raise NotImplementedError("Phase 1")
