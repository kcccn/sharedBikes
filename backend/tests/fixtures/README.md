# Test Fixtures

This directory contains test data fixtures for the sharedBikes test suite.

## Directory Structure

```
fixtures/
├── README.md          # This file — fixture conventions
└── osm/               # OpenStreetMap XML data snippets
    ├── small_grid.osm     # 3×3 grid (9 nodes, 12 edges)
    ├── empty.osm          # Valid OSM XML with zero nodes/ways
    └── broken_ref.osm     # Way referencing non-existent node
```

## Conventions

1. **Fixture files are checked into git.** Keep them small (< 50 KB) so they
   remain fast to load in CI.
2. **Use hand-crafted OSM XML** rather than real-world extracts for unit and
   integration tests. This guarantees deterministic behavior.
3. **Name fixtures descriptively.** Each fixture should make its edge case
   obvious from the file name.
4. **Add a comment header** inside each `.osm` file describing what it
   represents and what test scenario it exercises.

## Adding a New Fixture

1. Create the file under the appropriate subdirectory (e.g., `osm/`).
2. Add a comment header with a brief description.
3. Update this README table of contents if adding a new subdirectory.
