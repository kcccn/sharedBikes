---
name: phase-a-abstract-coord-complete
description: Phase A Complete — Abstract Coord + ProceduralCityGenerator
metadata:
  type: knowledge
  tags: [phase-a, coord, procedural, osm-deprecation, architecture]
  status: active
  created: 2026-05-12T09:06:09Z
  updated: 2026-05-12T10:18:49Z
---

# Phase A Complete — Abstract Coord + ProceduralCityGenerator

Phase A of architecture decision (#139) is complete and **merged** (PR #141, squash `ba01a87`).

### Changes landed:
- All LatLng usage replaced with Coord(x, y) from `app/core/coord.py`
- Haversine distance → Euclidean via `Coord.distance_to()`
- OSM parsing deprecated (`osm_parser.py` public functions raise `OSMError`)
- `ProceduralCityGenerator` handles seed-based city generation
- `map_service.py` — config-driven procedural only, no OSM fallback
- All tests migrated: 16 files changed, ~235 lines net

### Bugs caught & fixed during review:
1. `_build_city` was hardcoding 35×35 grid → now reads `config.procedural.grid_rows/cols/spacing/jitter`
2. Dead `_build_zones` method removed

### Next (Phase B):
Frontend Canvas rendering — Leaflet → abstract canvas. Not started.
