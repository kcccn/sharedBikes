"""Station auto-generation from road network topology.

Algorithm overview
------------------
1. Compute node degree (how many edges connect to each node) — a proxy
   for intersection importance.
2. Sort nodes by degree descending; higher-degree nodes make better
   station locations.
3. Greedy placement with a minimum-distance constraint (default 300 m)
   to avoid clustering.
4. Capacity is assigned proportional to node degree within configured
   bounds.
"""

from __future__ import annotations

import math

from app.core.city import Edge, LatLng, Node, Station


# ---- helpers (local copies to keep module self-contained) ----

def _haversine_km(a: LatLng, b: LatLng) -> float:
    R = 6371.0
    dlat = math.radians(b.lat - a.lat)
    dlng = math.radians(b.lng - a.lng)
    sin_dlat = math.sin(dlat / 2)
    sin_dlng = math.sin(dlng / 2)
    h = sin_dlat * sin_dlat + math.cos(math.radians(a.lat)) * math.cos(math.radians(b.lat)) * sin_dlng * sin_dlng
    return 2 * R * math.atan2(math.sqrt(h), math.sqrt(1 - h))


# ---- public API ----


def generate_stations(
    nodes: dict[str, Node],
    edges: dict[str, Edge],
    *,
    min_distance_km: float = 0.3,
    min_capacity: int = 10,
    max_capacity: int = 50,
    max_stations: int | None = None,
) -> dict[str, Station]:
    """Auto-place bike stations on a road network.

    Parameters
    ----------
    nodes:
        Road-network nodes keyed by node_id.
    edges:
        Road segments keyed by edge_id.  Used to compute node degree.
    min_distance_km:
        Minimum distance between stations in km (default 0.3 km).
    min_capacity:
        Smallest capacity for any station.
    max_capacity:
        Largest capacity for any station.
    max_stations:
        Hard upper bound on station count (None = unlimited).

    Returns
    -------
    dict[str, Station]
        Generated stations keyed by station_id (prefixed ``"station-auto-"``).
    """
    if not nodes:
        return {}

    # 1. Compute node degree from edges
    degree: dict[str, int] = {}
    for node_id in nodes:
        degree[node_id] = 0
    for edge in edges.values():
        degree[edge.from_node] = degree.get(edge.from_node, 0) + 1
        degree[edge.to_node] = degree.get(edge.to_node, 0) + 1

    # 2. Sort candidate nodes by degree descending
    candidates: list[tuple[str, int]] = sorted(
        degree.items(), key=lambda x: x[1], reverse=True
    )

    # If we have max_degree == 0 (no edges at all), fall back to spatial grid
    if not candidates or max(d for _, d in candidates) == 0:
        return _grid_fallback(nodes, min_distance_km, min_capacity, max_capacity, max_stations)

    max_degree = candidates[0][1]

    # 3. Greedy placement
    placed: list[LatLng] = []
    stations: dict[str, Station] = {}
    max_deg_norm = max(max_degree, 1)

    for node_id, deg in candidates:
        node = nodes[node_id]
        pos = node.position

        # Enforce minimum distance
        too_close = any(
            _haversine_km(pos, p) < min_distance_km for p in placed
        )
        if too_close:
            continue

        # Capacity scales with node degree
        ratio = deg / max_deg_norm
        capacity = min_capacity + int(round(ratio * (max_capacity - min_capacity)))
        capacity = max(min_capacity, min(max_capacity, capacity))

        station_id = f"station-auto-{node_id}"
        stations[station_id] = Station(
            station_id=station_id,
            position=pos,
            capacity=capacity,
            name=f"Station at {pos.lat:.4f}, {pos.lng:.4f}",
        )
        placed.append(pos)

        if max_stations is not None and len(stations) >= max_stations:
            break

    return stations


def _grid_fallback(
    nodes: dict[str, Node],
    min_distance_km: float,
    min_capacity: int,
    max_capacity: int,
    max_stations: int | None,
) -> dict[str, Station]:
    """Fallback when no edge data is available: place stations on a
    subsampled grid of node positions."""
    if not nodes:
        return {}

    # Simple spatial subsampling: sort by lat then greedily place
    sorted_nodes = sorted(nodes.values(), key=lambda n: (n.position.lat, n.position.lng))

    placed: list[LatLng] = []
    stations: dict[str, Station] = {}
    for node in sorted_nodes:
        pos = node.position
        too_close = any(
            _haversine_km(pos, p) < min_distance_km for p in placed
        )
        if too_close:
            continue
        stations[f"station-auto-{node.node_id}"] = Station(
            station_id=f"station-auto-{node.node_id}",
            position=pos,
            capacity=(min_capacity + max_capacity) // 2,
            name=f"Station at {pos.lat:.4f}, {pos.lng:.4f}",
        )
        placed.append(pos)
        if max_stations is not None and len(stations) >= max_stations:
            break

    return stations
