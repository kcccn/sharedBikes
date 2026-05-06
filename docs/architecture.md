# Project Architecture — CityBike-Sim

## Layered Architecture

```
┌─────────────────────────────────────────────┐
│              FastAPI (app/main.py)            │  Entry point
├─────────────────────────────────────────────┤
│           API v1 (app/api/v1/router.py)      │  HTTP layer (thin)
├─────────────────────────────────────────────┤
│        Service Layer (app/services/)          │  Business orchestration
├─────────────────────────────────────────────┤
│          Core Domain (app/core/)              │  Pure domain logic
│  ┌───────┐ ┌───────┐ ┌────────┐ ┌────────┐  │
│  │ City  │ │ Fleet │ │Weather │ │Engine  │  │
│  └───────┘ └───────┘ └────────┘ └────────┘  │
├─────────────────────────────────────────────┤
│        Utils (app/utils/)                     │  Geo, math helpers
└─────────────────────────────────────────────┘
```

### Dependency Direction

```
main.py → api/ → services/ → core/ ← utils/
                              ↑
                         models/ (DTOs)
```

**Key rule:** `core/` never imports from `api/`, `services/`, or `models/`. It only depends on `utils/` and stdlib.

## Data Flow (One Tick)

```
1. WeatherGenerator.generate(tick)  → Environment
2. DemandService.generate_requests() → TripRequest[]
3. Fleet processes requests (dock/undock)
4. (Optional) RebalanceStrategy.analyse() → DispatchOrder[]
5. Fleet.snapshot() → FleetSnapshot (consumed by API / viz)
```

## Domain Models

| Model | Mutability | Description |
|-------|-----------|-------------|
| `City` | Immutable (built once) | Road network + stations + zones |
| `Node` / `Edge` | Immutable | Network topology |
| `Station` | Mutable (inventory changes) | Docking point with capacity |
| `Bike` | Mutable | Single bike lifecycle |
| `Fleet` | Mutable aggregate | All bikes + station inventory |
| `FleetSnapshot` | Immutable | Point-in-time read model |
| `Environment` | Immutable per tick | Weather + events |
| `SimulationEngine` | Stateful | Manages tick loop |

## Phase Breakdown

| Phase | Focus | Key Deliverables |
|-------|-------|-----------------|
| 0 | Skeleton (this PR) | Project structure, domain models, stubs, tests |
| 1 | Map ingestion | OSM parsing (osmium/osmnx), city loading |
| 2 | Demand generation | Commuter tides, weather scaling, trip lifecycle |
| 3 | Fleet rebalancing | Truck routing, dispatch execution, cost tracking |
| 4 | Visualization | Deck.gl heatmap + OD flow rendering |

## Configuration

All settings are managed through `AppConfig` (pydantic-settings). Environment variables prefixed with `CITYBIKE_` override defaults.

```bash
CITYBIKE_HOST=0.0.0.0
CITYBIKE_PORT=8000
CITYBIKE_DEBUG=true
```
