---
name: abstract-coord-architecture-decision
description: Phase 7: Abstract Coord Architecture — No Fake Realism
metadata:
  type: knowledge
  tags: [architecture, phase-7, abstract-coord, osm-cleanup, founder-decision]
  status: active
  created: 2026-05-12T08:54:46Z
  updated: 2026-05-12T08:54:46Z
---

# Phase 7: Abstract Coord Architecture — No Fake Realism

## Decision

Kill OSM/LatLng/Leaflet. Full abstract coordinate system. No two-layer compromise.

## Why

Fake realism (OSM tiles + no real routing + no real parking data) is worse than honest abstraction. The founder called this out correctly.

## What Changed

- **LatLng** (defined in 3 places) → single `Coord(x, y)` in `app/core/coord.py`
- **Haversine distance** → Euclidean distance (abstract grid, not spherical)
- **OSM parser** → **Deleted**. No more `osm_parser.py`, `parse_from_bbox`, `parse_from_file`, `parse_from_place`
- **Synthetic grid** (still LatLng-based) → `ProceduralCityGenerator` — seed-driven abstract grid, no geographic constraints
- **MapService** — rewritten to use ProceduralCityGenerator as primary path, no OSM fallbacks
- **Frontend** (Leaflet) → To be replaced by Canvas/SVG abstract rendering (Phase B)

## What Stayed Untouched

Engine, Scheduler, Economy, Demand, AchievementEngine, Leaderboard — none directly use LatLng.

## Execution

Phase A (backend): dispatched to coder on #139, branch `phase-a-abstract-coord`
Phase B (frontend): Canvas rendering, TBD

Ref: Issue #139, architectural decision by Ryo Architect
