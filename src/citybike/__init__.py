"""
CityBike-Sim: Urban Bike Sharing Operations Simulator.

Architecture: Event-Sourced Modular Monolith
---------------------------------------------
The simulation is built around an immutable event log. Every state mutation
(ride started, bike returned, rebalancing trip completed, weather changed)
is a typed domain event. The current world state is a pure fold over the
event stream, enabling deterministic replay, time travel debugging, and
seamless integration with OD flow visualizations.

Layers (bottom to top):
  1. core/         — Pure domain models, events, and simulation clock
  2. geography/    — OSM data ingestion, road networks, routing
  3. demand/       — NPC trip generation from commute patterns
  4. dispatch/     — Fleet rebalancing strategies & algorithms
  5. simulation/   — Game loop, state management, snapshot isolation
  6. analytics/    — Materialized views (heatmaps, KPIs) from event stream
  7. api/          — FastAPI layer for frontend consumption
"""

__version__ = "0.1.0"
