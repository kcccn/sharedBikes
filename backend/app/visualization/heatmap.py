"""Heatmap data generation — supply-demand intensity map."""

from __future__ import annotations

from app.core.city import City
from app.core.fleet import FleetSnapshot


def generate_heatmap(
    city: City,
    snapshot: FleetSnapshot,
    tick: int,
) -> list[dict]:
    """Generate heatmap points representing supply-demand intensity.

    Phase 4 goal: produce weighted point data for Deck.gl screen-grid
    or heatmap layer rendering.
    """
    _ = city, snapshot, tick
    return []  # stub
