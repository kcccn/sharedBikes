"""ProceduralCityGenerator — seed-based abstract city generation.

Generates a road network on an abstract 2D grid using ``Coord(x, y)``.
No external map data (OSM, GIS) is required. The generator is fully
deterministic given the same seed and parameters.

The output is a ``City`` with nodes, edges, zones, and optionally stations,
ready for the simulation engine.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from app.core.city import City, Coord, Edge, Node, Station, Zone
from app.core.city_config import CityConfig
from app.core.station_generator import generate_stations


@dataclass
class ProceduralCityGenerator:
    """Generates an abstract grid-based city from a seed.

    Parameters
    ----------
    seed : int
        Random seed for reproducibility (default 42).
    grid_rows : int
        Number of rows in the node grid (default 35).
    grid_cols : int
        Number of columns in the node grid (default 35).
    spacing : float
        Distance between adjacent grid nodes (default 1.0).
    jitter : float
        Maximum random offset applied to node positions (default 0.1).
    """

    seed: int = 42
    grid_rows: int = 35
    grid_cols: int = 35
    spacing: float = 1.0
    jitter: float = 0.1

    def generate(
        self,
        config: CityConfig | None = None,
    ) -> City:
        """Generate a ``City`` from procedural parameters.

        If *config* is provided, station generation settings are read
        from it. Otherwise default station generation is used.
        """
        rng = random.Random(self.seed)

        nodes = self._generate_nodes(rng)
        edges = self._generate_edges(nodes, rng)
        zones = self._generate_zones(nodes)

        # Station generation
        stations: dict[str, Station] = {}
        if config and config.station_generation.enabled:
            stations = generate_stations(
                nodes,
                edges,
                min_distance=config.station_generation.min_distance_km,
                min_capacity=config.station_generation.min_capacity,
                max_capacity=config.station_generation.max_capacity,
                max_stations=config.station_generation.max_stations,
            )
        elif config is None:
            # Default: generate some stations
            stations = generate_stations(
                nodes,
                edges,
                min_distance=1.5,
                min_capacity=10,
                max_capacity=50,
            )

        return City(nodes=nodes, edges=edges, stations=stations, zones=zones)

    # ── internal node/edge generation ──────────────────────────────

    def _generate_nodes(self, rng: random.Random) -> dict[str, Node]:
        """Generate a grid of nodes with jitter."""
        nodes: dict[str, Node] = {}
        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                node_id = f"n_{r}_{c}"
                x = c * self.spacing + rng.uniform(-self.jitter, self.jitter)
                y = r * self.spacing + rng.uniform(-self.jitter, self.jitter)
                nodes[node_id] = Node(
                    node_id=node_id,
                    position=Coord(x=round(x, 4), y=round(y, 4)),
                    elevation_m=round(rng.uniform(0, 50), 1),
                )
        return nodes

    def _generate_edges(
        self,
        nodes: dict[str, Node],
        rng: random.Random,
    ) -> dict[str, Edge]:
        """Generate bidirectional edges between adjacent grid nodes."""
        edges: dict[str, Edge] = {}
        edge_id = 0

        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                nid = f"n_{r}_{c}"
                pos = nodes[nid].position

                # Horizontal edge (right)
                if c + 1 < self.grid_cols:
                    nid_r = f"n_{r}_{c+1}"
                    pos_r = nodes[nid_r].position
                    dist = pos.distance_to(pos_r)
                    speed = rng.choice([30, 40, 50])
                    for direction in [(nid, nid_r), (nid_r, nid)]:
                        edges[f"e_{edge_id}"] = Edge(
                            edge_id=f"e_{edge_id}",
                            from_node=direction[0],
                            to_node=direction[1],
                            length_m=round(dist, 2),
                            max_speed_kmh=float(speed),
                        )
                        edge_id += 1

                # Vertical edge (down)
                if r + 1 < self.grid_rows:
                    nid_d = f"n_{r+1}_{c}"
                    pos_d = nodes[nid_d].position
                    dist = pos.distance_to(pos_d)
                    speed = rng.choice([30, 40, 50])
                    for direction in [(nid, nid_d), (nid_d, nid)]:
                        edges[f"e_{edge_id}"] = Edge(
                            edge_id=f"e_{edge_id}",
                            from_node=direction[0],
                            to_node=direction[1],
                            length_m=round(dist, 2),
                            max_speed_kmh=float(speed),
                        )
                        edge_id += 1

        return edges

    def _generate_zones(self, nodes: dict[str, Node]) -> dict[str, Zone]:
        """Generate 4 quadrant zones from the grid."""
        if not nodes:
            return {}

        # Find grid extents
        xs = [n.position.x for n in nodes.values()]
        ys = [n.position.y for n in nodes.values()]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        x_mid = (x_min + x_max) / 2
        y_mid = (y_min + y_max) / 2

        zones: dict[str, Zone] = {
            "northwest": Zone(
                zone_id="northwest",
                name="Northwest",
                polygon=[
                    Coord(x_min, y_mid),
                    Coord(x_mid, y_mid),
                    Coord(x_mid, y_max),
                    Coord(x_min, y_max),
                ],
            ),
            "northeast": Zone(
                zone_id="northeast",
                name="Northeast",
                polygon=[
                    Coord(x_mid, y_mid),
                    Coord(x_max, y_mid),
                    Coord(x_max, y_max),
                    Coord(x_mid, y_max),
                ],
            ),
            "southwest": Zone(
                zone_id="southwest",
                name="Southwest",
                polygon=[
                    Coord(x_min, y_min),
                    Coord(x_mid, y_min),
                    Coord(x_mid, y_mid),
                    Coord(x_min, y_mid),
                ],
            ),
            "southeast": Zone(
                zone_id="southeast",
                name="Southeast",
                polygon=[
                    Coord(x_mid, y_min),
                    Coord(x_max, y_min),
                    Coord(x_max, y_mid),
                    Coord(x_mid, y_mid),
                ],
            ),
        }
        return zones
