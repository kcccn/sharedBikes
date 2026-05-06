"""OSM data parser — converts OSM road networks to Core domain models.

Supports three input sources:
- Place name (via Nominatim geocoding + osmnx)
- Bounding box coordinates
- Local .osm.pbf / .osm XML file
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import networkx as nx

from app.core.city import City, Edge, LatLng, Node, Station, Zone

logger = logging.getLogger(__name__)

# The only highway types we accept per the Phase-1 spec.
ALLOWED_HIGHWAYS = frozenset({
    "primary",
    "secondary",
    "tertiary",
    "residential",
})

# osmnx custom_filter: download only the roads we care about.
OSMX_HIGHWAY_FILTER = '["highway"~"primary|secondary|tertiary|residential"]'


class OSMError(Exception):
    """Raised when OSM data cannot be parsed or is invalid."""


def parse_from_place(
    place_name: str,
    *,
    simplify: bool = True,
    retain_all: bool = False,
) -> City:
    """Download and parse OSM road network for a named place (e.g. \"Beijing, China\").

    Parameters
    ----------
    place_name:
        A place name Nominatim can geocode.
    simplify:
        Whether osmnx should simplify the graph (merge interstitial nodes).
    retain_all:
        If True, keep all graph components; if False, drop smaller disconnected
        subgraphs and retain only the largest strongly connected component.

    Returns
    -------
    A fully populated ``City`` with nodes and edges.

    Raises
    ------
    OSMError
        If the place cannot be resolved or the graph is empty after filtering.
    """
    _ensure_osmnx()

    try:
        import osmnx as ox

        G = ox.graph_from_place(
            place_name,
            network_type="drive",
            custom_filter=OSMX_HIGHWAY_FILTER,
            simplify=simplify,
            retain_all=retain_all,
        )
    except Exception as exc:
        raise OSMError(f"Failed to download OSM data for {place_name!r}: {exc}") from exc

    return _graph_to_city(G)


def parse_from_bbox(
    north: float,
    south: float,
    east: float,
    west: float,
    *,
    simplify: bool = True,
    retain_all: bool = False,
) -> City:
    """Download and parse OSM road network within a bounding box.

    Parameters
    ----------
    north, south, east, west:
        Bounding box coordinates in WGS84 degrees.
    simplify, retain_all:
        See ``parse_from_place``.

    Returns
    -------
    A fully populated ``City`` with nodes and edges.

    Raises
    ------
    OSMError
        If the bbox is invalid or the graph is empty after filtering.
    """
    _ensure_osmnx()

    if south >= north or west >= east:
        raise OSMError(
            f"Invalid bounding box: north={north} must be > south={south}, "
            f"east={east} must be > west={west}"
        )

    try:
        import osmnx as ox

        G = ox.graph_from_bbox(
            north=north,
            south=south,
            east=east,
            west=west,
            network_type="drive",
            custom_filter=OSMX_HIGHWAY_FILTER,
            simplify=simplify,
            retain_all=retain_all,
        )
    except Exception as exc:
        raise OSMError(
            f"Failed to download OSM data for bbox "
            f"(n={north}, s={south}, e={east}, w={west}): {exc}"
        ) from exc

    return _graph_to_city(G)


def parse_from_file(filepath: str | Path, *, simplify: bool = True) -> City:
    """Parse a local ``.osm.pbf`` or ``.osm`` XML file.

    Parameters
    ----------
    filepath:
        Path to the OSM file on disk.
    simplify:
        Whether osmnx should simplify the graph.

    Returns
    -------
    A fully populated ``City`` with nodes and edges.

    Raises
    ------
    OSMError
        If the file does not exist or the graph is empty.
    """
    _ensure_osmnx()

    path = Path(filepath)
    if not path.exists():
        raise OSMError(f"OSM file not found: {path}")

    try:
        import osmnx as ox

        G = ox.graph_from_xml(str(path), simplify=simplify)
    except Exception as exc:
        raise OSMError(f"Failed to parse OSM file {path}: {exc}") from exc

    return _graph_to_city(G)


# ---------------------------------------------------------------------------
# Internal: osmnx NetworkX MultiDiGraph → City domain model
# ---------------------------------------------------------------------------


def _graph_to_city(G: nx.MultiDiGraph) -> City:
    """Convert an osmnx street-network graph to a ``City`` domain object.

    This function is **idempotent** with respect to OSM data quality:
    - Nodes missing coordinates are silently skipped.
    - Edges whose ``source`` or ``target`` node was skipped are dropped.
    - Edges whose ``highway`` tag is absent or not in the allowed set are
      dropped (belt-and-suspenders — ``osmnx`` already filters, but local
      files might not).
    - ``maxspeed`` values are parsed from various OSM formats (``"50"``,
      ``"50 km/h"``, ``"30 mph"``, lists thereof).
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
            position=LatLng(lat=float(lat), lng=float(lon)),
            elevation_m=float(elevation) if elevation is not None else 0.0,
        )
        nodes[node.node_id] = node

    # ── Build edge map ────────────────────────────────────────────────
    for u, v, key, data in G.edges(keys=True, data=True):
        # Belt-and-suspenders highway filter for local-file parsing.
        highway_val = data.get("highway")
        if not _highway_allowed(highway_val):
            continue

        su = str(u)
        sv = str(v)

        # Skip edges whose endpoints were dropped.
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


# ── Helpers ─────────────────────────────────────────────────────────────


def _ensure_osmnx() -> None:
    """Check osmnx is importable; raise a helpful OSMError if not."""
    try:
        import osmnx  # noqa: F401
    except ImportError:
        raise OSMError(
            "osmnx is required but not installed. Run: pip install osmnx"
        )


def _highway_allowed(highway_val: Any) -> bool:
    """Check whether an OSM ``highway`` tag value is in our allowed set.

    osmnx sometimes returns a *list* of highway values (e.g. ``["primary",
    "trunk"]``) for a single edge when the road changes classification.
    We accept the edge if *any* value in the list is allowed.
    """
    if isinstance(highway_val, list):
        return any(h in ALLOWED_HIGHWAYS for h in highway_val)
    return highway_val in ALLOWED_HIGHWAYS


def _parse_maxspeed(raw: Any) -> float:
    """Parse an OSM ``maxspeed`` tag into a float (km/h).

    Handles the common OSM representations:
    - ``None`` / missing → 30 km/h (urban default)
    - numeric string → ``float(s)``
    - ``"50 km/h"``, ``"30 mph"`` → converted to km/h
    - ``["50", "60"]`` → takes the *minimum* (conservative)
    """
    if raw is None:
        return 30.0

    if isinstance(raw, list):
        speeds = []
        for item in raw:
            speeds.append(_parse_single_maxspeed(item))
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
