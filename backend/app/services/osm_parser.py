"""OSM data parser — DEPRECATED.

All OSM parsing entry points (``parse_from_place``, ``parse_from_bbox``,
``parse_from_file``) raise ``OSMError`` with a clear message. The internal
helper functions (``_graph_to_city``, ``_highway_allowed``, ``_parse_maxspeed``,
etc.) are preserved for backward-compatible unit-testing but are not intended
for production use.

Cities are now generated procedurally — see :class:`ProceduralCityGenerator`.
This entire module will be removed after Phase B (frontend migration).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from app.core.city import City, Coord, Edge, Node, Station, Zone

logger = logging.getLogger(__name__)


class OSMError(Exception):
    """Raised when OSM data cannot be parsed or is invalid."""


def parse_from_place(
    place_name: str,
    *,
    simplify: bool = True,
    retain_all: bool = False,
):
    """Deprecated. OSM parsing has been removed."""
    raise OSMError(
        f"OSM parsing is no longer supported. "
        f"Cities are now generated procedurally. "
        f"Requested place: {place_name!r}"
    )


def parse_from_bbox(
    north: float,
    south: float,
    east: float,
    west: float,
    *,
    simplify: bool = True,
    retain_all: bool = False,
):
    """Deprecated. OSM parsing has been removed."""
    raise OSMError(
        f"OSM parsing is no longer supported. "
        f"Cities are now generated procedurally. "
        f"Bounding box: N={north}, S={south}, E={east}, W={west}"
    )


def parse_from_file(filepath: str | Path, *, simplify: bool = True):
    """Deprecated. OSM parsing has been removed."""
    raise OSMError(
        f"OSM parsing is no longer supported. "
        f"Cities are now generated procedurally. "
        f"Requested file: {filepath}"
    )


# ---------------------------------------------------------------------------
# Internal helpers (preserved for backward-compatible testing)
# ---------------------------------------------------------------------------


# The highway types we accept per the Phase-1 spec.
ALLOWED_HIGHWAYS = frozenset({
    "primary",
    "secondary",
    "tertiary",
    "residential",
})


def _graph_to_city(G: Any) -> City:
    """Convert an osmnx street-network graph to a ``City`` domain object.

    .. deprecated::
        This function is retained only for existing unit tests.
        OSM parsing is no longer supported for production use.
    """
    nodes: dict[str, Node] = {}
    edges: dict[str, Edge] = {}

    # ── Build node map ────────────────────────────────────────────────
    for osmid, data in G.nodes(data=True):
        lat = data.get("y")
        lon = data.get("x")
        if lat is None or lon is None:
            logger.warning("Skipping node %s: missing coordinates", osmid)
            continue

        elevation = data.get("elevation")
        node = Node(
            node_id=str(osmid),
            position=Coord(x=float(lon), y=float(lat)),
            elevation_m=float(elevation) if elevation is not None else 0.0,
        )
        nodes[node.node_id] = node

    # ── Build edge map ────────────────────────────────────────────────
    for u, v, key, data in G.edges(keys=True, data=True):
        highway_val = data.get("highway")
        if not _highway_allowed(highway_val):
            continue

        su = str(u)
        sv = str(v)

        if su not in nodes or sv not in nodes:
            logger.debug("Dropping edge %s→%s (missing endpoint in node map)", u, v)
            continue

        edge_id = f"{su}→{sv}#{key}"
        length_m = data.get("length", 0.0)
        max_speed = _parse_maxspeed(data.get("maxspeed"))

        edges[edge_id] = Edge(
            edge_id=edge_id,
            from_node=su,
            to_node=sv,
            length_m=float(length_m),
            max_speed_kmh=max_speed,
        )

    if not nodes:
        raise OSMError("Graph is empty — no valid nodes found after filtering")
    if not edges:
        raise OSMError("Graph is empty — no valid edges found after filtering")

    return City(
        nodes=nodes,
        edges=edges,
        stations={},
        zones={},
    )


def _highway_allowed(highway_val: Any) -> bool:
    """Check whether an OSM ``highway`` tag value is in our allowed set."""
    if isinstance(highway_val, list):
        return any(h in ALLOWED_HIGHWAYS for h in highway_val)
    return highway_val in ALLOWED_HIGHWAYS


def _parse_maxspeed(raw: Any) -> float:
    """Parse an OSM ``maxspeed`` tag into a float (km/h)."""
    if raw is None:
        return 30.0

    if isinstance(raw, list):
        speeds = [_parse_single_maxspeed(item) for item in raw]
        return min(speeds) if speeds else 30.0

    return _parse_single_maxspeed(raw)


_MPH_TO_KMH = 1.609344
_SPEED_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(km/h|kph|mph)?", re.IGNORECASE)


def _parse_single_maxspeed(val: str | float) -> float:
    """Parse a single maxspeed value."""
    if isinstance(val, (int, float)):
        return float(val)

    match = _SPEED_PATTERN.match(str(val).strip())
    if not match:
        logger.debug("Unrecognised maxspeed format: %r, falling back to 30 km/h", val)
        return 30.0

    number = float(match.group(1))
    unit = (match.group(2) or "").lower()

    if unit in ("mph",):
        return round(number * _MPH_TO_KMH, 1)
    return number
