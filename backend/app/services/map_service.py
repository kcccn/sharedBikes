"""City & map loading service."""

from __future__ import annotations

from app.core.city import City


class MapService:
    """Loads and manages city geodata.

    Phase 1: Replace stub with osmium/osmnx real OSM data parsing.
    """

    def __init__(self) -> None:
        self._city: City | None = None

    @property
    def city(self) -> City | None:
        return self._city

    async def load_city(self, name: str = "default") -> City:
        """Load city data — stub returning a minimal city.

        TODO(phase-1): parse real OSM data with osmnx/osmium.
        """
        from app.core.city import Node, Station, Zone, LatLng

        station = Station(
            station_id="st-001",
            name="Central Hub",
            position=LatLng(39.9042, 116.4074),
            capacity=30,
        )
        city = City(
            nodes={"n1": Node("n1", LatLng(39.9042, 116.4074))},
            edges={},
            stations={"st-001": station},
            zones={"downtown": Zone("downtown", "Downtown", (LatLng(39.90, 116.40),))},
        )
        self._city = city
        return city

    def get_city(self) -> City | None:
        return self._city
