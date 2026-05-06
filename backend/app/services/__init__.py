"""Service layer stubs — orchestration logic lives here."""


class MapService:
    """Handles city / road-network loading from OSM data."""

    async def load_city(self, city_id: str) -> None:
        """Load city from OSM or a serialised cache."""
        raise NotImplementedError


class DemandService:
    """Generates NPC trip demand based on time, weather, and events."""

    async def generate_trips(self, tick: int) -> list[dict]:
        """Return a list of trip requests for the given tick."""
        raise NotImplementedError


class BalanceService:
    """Orchestrates rebalancing analysis and dispatch."""

    async def run_rebalance(self) -> list[dict]:
        """Run the rebalancing strategy and return dispatch orders."""
        raise NotImplementedError
