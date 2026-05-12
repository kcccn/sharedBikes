"""OSM data parser — DEPRECATED.

All OSM-related functionality has been removed.
Cities are now generated procedurally — see :class:`ProceduralCityGenerator`.

This module exists only as a stub that raises ``OSMError`` with a clear
message. It will be removed entirely after Phase B (frontend migration).
"""

from __future__ import annotations

from pathlib import Path


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
