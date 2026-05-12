---
name: heatmap-demand-factor-pattern
description: Phase 6 P2: Heatmap — demand_factor + Leaflet.heat
metadata:
  type: knowledge
  tags: [phase6, heatmap, frontend, leaflet]
  status: active
  created: 2026-05-12T04:12:53Z
  updated: 2026-05-12T04:12:53Z
---

# Phase 6 P2: Heatmap — demand_factor + Leaflet.heat

## Architecture

Station-level demand heatmap computed from `StationStatsTracker` in-memory counters.

### demand_factor computation
`trips_completed / max(trips_completed)` → [0.0, 1.0] per station. Zero trips → 0.0. Hottest station → 1.0. Pure Python, no DB.

### Delivery paths
1. **WebSocket push**: `_serialize_tick()` in `ws.py` injects `demand_factors` dict on every tick message. Frontend Leaflet.heat layer calls `setLatLngs()`.
2. **REST fallback**: `GET /dashboard/heatmap` returns `HeatmapCell[]` (lat, lng, intensity) for non-WS clients.

### Frontend
- Leaflet.heat CDN from unpkg (same delivery as Leaflet itself — no npm)
- Gradient: blue (0.0) → lime → yellow → orange → red (1.0)
- Radius: 28px, blur: 18px, maxZoom: 17

### Key invariant
No new EventBus subscriptions, no DB writes, no Engine pipeline changes. Pure query-side feature on existing counter data.
