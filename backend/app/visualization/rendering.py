"""Visualization stub — to be implemented in Phase 4."""

from app.core.fleet import FleetSnapshot


def generate_heatmap_data(snapshot: FleetSnapshot) -> dict:
    """Return station-level heatmap payload."""
    raise NotImplementedError("Phase 4")


def generate_od_flows(snapshot: FleetSnapshot) -> list[dict]:
    """Return origin–destination flow lines."""
    raise NotImplementedError("Phase 4")
