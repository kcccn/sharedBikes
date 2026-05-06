"""Heatmap generation for demand visualisation (stub)."""

from app.core.city import City
from app.core.fleet import FleetSnapshot


def generate_heatmap_cells(
    fleet_snapshot: FleetSnapshot,
    city: City,
) -> list[dict]:
    """Generate heatmap cells from fleet state.
    
    Phase 2+: real grid aggregation.
    """
    _ = fleet_snapshot, city
    return []


def generate_od_flows(
    trip_history: list,
    city: City,
) -> list[dict]:
    """Generate origin-destination flow lines.
    
    Phase 3+: real trip log aggregation.
    """
    _ = trip_history, city
    return []
