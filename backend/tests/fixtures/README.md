# Test Fixtures

This directory holds static test data for integration tests.

## Directory Structure

```
fixtures/
├── README.md
└── osm/
    ├── small_grid.osm       # 3×3 grid road network (~1km²)
    ├── empty.osm            # Valid OSM XML with zero roads
    └── broken_ref.osm       # Way references a non-existent node
```

## OSM Fixtures

Each `.osm` file is a hand-crafted OSM XML snippet (no external dependencies).
They are designed to be parsed by `app.services.osm_parser.parse_from_file()`.

### `small_grid.osm`

A 3×3 intersection grid covering approximately 1 km².

| Property | Value |
|----------|-------|
| Nodes    | 9     |
| Ways     | 6     |
| Edges    | 12 (bidirectional) |
| Area     | ~0.6 km² |
| Highways | `residential`, `secondary` |

Use this to verify:
- Basic node/edge parsing
- Strong connectivity (the grid is fully connected)
- Performance baseline (< 5 s / 1 km²)

### `empty.osm`

A valid OSM XML file with `<osm>` root and `<bounds>` but zero nodes/ways.

Use this to verify graceful handling of empty data.

### `broken_ref.osm`

An OSM XML file where a `<way>` references a `<nd ref="9999">` that does not
exist in the node list.

Use this to verify graceful handling of broken/corrupted data.
