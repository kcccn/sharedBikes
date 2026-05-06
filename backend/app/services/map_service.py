"""Map service — loads real OSM data and builds the City model."""

from __future__ import annotations

from app.core.city import City


class MapService:
    """Loads, caches, and serves the city road network.

    Phase 1 goal: parse real OpenStreetMap data using osmium/osmnx
    and construct a ``City`` instance with nodes, edges, stations, and zones.
    """

    def __init__(self) -> None:
        self._city: City | None = None

    async def load_city(self, city_id: str) -> City:
        """Load (or retrieve from cache) the city definition."""
        _ = city_id
        raise NotImplementedError("Phase 1: implement OSM data ingestion")

    def get_city(self) -> City | None:
        """Return the currently loaded city, or ``None``."""
        return self._city
