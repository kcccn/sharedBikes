"""Origin-destination flow generation — trip trajectory data."""

from __future__ import annotations

from app.core.city import City
from app.core.fleet import FleetSnapshot


def generate_flows(
    city: City,
    snapshot: FleetSnapshot,
    tick: int,
) -> list[dict]:
    """Generate OD flow lines showing completed trip volumes.

    Phase 4 goal: produce arc/polyline data for Deck.gl TripsLayer or
    GreatCircleLayer animation.
    """
    _ = city, snapshot, tick
    return []  # stub
