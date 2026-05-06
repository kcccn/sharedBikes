"""Map service — loads and caches City from OSM data."""

from app.core.city import City, LatLng, Node, Edge, Station, Zone


class MapService:
    """Service responsible for loading city map data."""

    def load_city(self, city_name: str) -> City:
        """Load or build a City from map data.
        
        Phase 1: stub returning a minimal test city.
        Phase 2+: real OSM parsing via osmium / osmnx.
        """
        # Temporary minimal city for testing
        center = LatLng(lat=39.9042, lng=116.4074)  # Beijing centre
        nodes = {
            "n1": Node(node_id="n1", position=center),
        }
        edges: dict[str, Edge] = {}
        stations: dict[str, Station] = {}
        zones: dict[str, Zone] = {}
        return City(nodes=nodes, edges=edges, stations=stations, zones=zones)
