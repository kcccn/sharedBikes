"""Visualisation data generators — produce frontend-ready payloads."""

from __future__ import annotations

from app.core.city import City
from app.core.fleet import FleetSnapshot


def build_heatmap(
    city: City, fleet_snapshot: FleetSnapshot
) -> list[dict[str, float]]:
    """Generate grid cells with normalised demand/supply intensity."""
    raise NotImplementedError("Phase 4 — Deck.gl heatmap integration")


def build_od_flows(
    recent_trips: list[tuple[str, str, int]],
) -> list[dict]:
    """Aggregate recent trips into origin-destination flow lines."""
    raise NotImplementedError("Phase 4 — OD flow animation")
