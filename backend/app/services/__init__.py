"""Business-logic services — I/O-aware operations."""

from __future__ import annotations

from app.core.city import City, LatLng, Station
from app.core.fleet import Fleet, Bike, BikeStatus


class MapService:
    """OSM data ingestion & city model construction."""

    async def load_city(self, name: str, osm_file: str) -> City:
        """Parse an OSM XML/PBF file and build a City graph.

        This is the heavy-lifting entry point — will delegate to
        osmium / osmnx in Phase 1 implementation.
        """
        raise NotImplementedError("Phase 1 — OSM integration")

    async def geocode(self, address: str) -> LatLng:
        raise NotImplementedError("Phase 1 — geocoding")


class DemandService:
    """NPC trip demand generation."""

    def generate_trip_requests(
        self, city: City, tick: int, multiplier: float = 1.0
    ) -> list[tuple[str, str]]:
        """Return list of (from_station_id, to_station_id) trip requests.

        Distribution is time-of-day and zone-type aware.
        """
        raise NotImplementedError("Phase 2 — demand simulation")


class BalanceService:
    """High-level fleet rebalancing orchestration."""

    def __init__(self, station_capacity: dict[str, int], fleet: Fleet):
        self._capacity = station_capacity
        self._fleet = fleet

    def suggest_rebalance(self) -> list[dict]:
        """Evaluate fleet state and return suggested dispatch orders."""
        raise NotImplementedError("Phase 2 — rebalancing logic")
