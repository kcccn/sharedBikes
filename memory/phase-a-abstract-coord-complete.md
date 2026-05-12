---
name: phase-a-abstract-coord-complete
description: Phase A Complete — Abstract Coord + ProceduralCityGenerator
metadata:
  type: knowledge
  tags: [phase-a, coord, procedural, osm-deprecation, architecture]
  status: active
  created: 2026-05-12T09:06:09Z
  updated: 2026-05-12T09:06:09Z
---

# Phase A Complete — Abstract Coord + ProceduralCityGenerator

Phase A of architecture decision (#139) is complete:
- All LatLng usage replaced with Coord(x, y) from app/core/coord.py
- haversine distance replaced with Euclidean distance via Coord.distance_to()
- OSM parsing deprecated (osm_parser.py public functions raise OSMError)
- ProceduralCityGenerator (app/services/procedural_city_generator.py) handles seed-based city generation
- map_service.py rewritten to use only procedural generation
- CityConfig replaced OSMConfig with ProceduralConfig
- API schemas changed lat/lng to x/y
- Default city is "default" (not "Beijing")
- PR #141 created, reviewer dispatched
- Phase B (frontend Canvas migration) is the next step
