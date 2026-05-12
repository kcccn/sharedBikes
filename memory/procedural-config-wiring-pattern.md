---
name: procedural-config-wiring-pattern
description: ProceduralCityGenerator must read grid params from CityConfig.procedural
metadata:
  type: knowledge
  tags: [procedural-generation, map-service, config-pattern, phase-a]
  status: active
  created: 2026-05-12T09:12:48Z
  updated: 2026-05-12T09:12:48Z
---

# ProceduralCityGenerator must read grid params from CityConfig.procedural

When wiring ProceduralCityGenerator into MapService._build_city, always pass config.procedural.grid_rows, grid_cols, spacing, and jitter. Hardcoding these values makes TOML config customization dead. Pattern:

```python
generator = ProceduralCityGenerator(
    seed=hash(config.city_id) % (2**31),
    grid_rows=config.procedural.grid_rows,
    grid_cols=config.procedural.grid_cols,
    spacing=config.procedural.spacing,
    jitter=config.procedural.jitter,
)
```

Also ensure _build_zones is either wired into the pipeline or removed — dead code that bypasses config.zone_configs is a trap.
