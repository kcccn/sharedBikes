"""PR description for Phase 0 architecture setup."""

This PR sets up the complete project skeleton for CityBike-Sim, establishing:

## ✅ What's included

### Backend (`backend/`)
- **FastAPI entry point** — `/health` endpoint, app factory
- **Centralized config** — `SimulationConfig` + `AppConfig` via pydantic-settings
- **Core domain models** (zero I/O dependencies):
  - `City` — immutable road network with `Node`, `Edge`, `Station`, `Zone`
  - `Fleet` / `FleetSnapshot` — mutable fleet with immutable point-in-time views
  - `Environment` / `SpecialEvent` — weather system with demand modifiers
  - `SimulationEngine` — tick-based main loop with state machine (CREATED → RUNNING → PAUSED → STOPPED)
  - `RebalanceStrategy` — strategy pattern with `GreedyThresholdStrategy`
- **Service stubs** — `MapService`, `DemandService`, `BalanceService` (Phase 1)
- **API v1 router** — 8 endpoint stubs covering city, fleet, simulation, dashboard
- **Pydantic DTO schemas** — `FleetSnapshotResponse`, `SimulationStatusResponse`, etc.
- **Geo utilities** — `haversine`, `bearing`, `midpoint`
- **Visualization stubs** — heatmap / OD flow generators (Phase 4)
- **Tests** — unit tests for city, engine, and geo utils
- **Tooling** — `pyproject.toml`, `ruff.toml`, `Makefile`, `requirements.txt`

### Docs
- `docs/architecture.md` — layered architecture diagram, dependency direction, data flow

## 🏗️ Architecture Decisions
- **Layered unidirectional dependencies**: `api/ → services/ → core/ ← utils/`
- **City is immutable** — built once, read-only after construction
- **Snapshot pattern** — `FleetSnapshot` for API consumption, mutable `Fleet` for performance
- **Pluggable rebalancing** — `RebalanceStrategy` interface, swappable implementations

## 🔜 Next Steps (Phase 1)
- Implement `MapService.load_city()` with osmium/osmnx
- Implement `DemandService` for commuter tide generation
- Replace API stubs with real service calls
