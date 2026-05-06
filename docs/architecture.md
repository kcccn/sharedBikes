# CityBike-Sim Architecture

## Layered Architecture

```
┌─────────────────────────────────────────────────────┐
│                     API Layer                        │
│   FastAPI router (app/api/v1/router.py)             │
│   Pydantic DTOs (app/models/schemas.py)             │
├─────────────────────────────────────────────────────┤
│                   Service Layer                      │
│   MapService  DemandService  BalanceService         │
│   (app/services/)                                   │
├─────────────────────────────────────────────────────┤
│                    Core Layer                        │
│   City  Fleet  Engine  Weather  Scheduler           │
│   (app/core/)  — pure domain logic, no I/O          │
├─────────────────────────────────────────────────────┤
│                Utilities / Shared                    │
│   geo.py  config.py  visualization/                 │
└─────────────────────────────────────────────────────┘
```

### Dependency Direction

**API → Services → Core ← Utils**

The core layer has zero I/O dependencies (no database, no network, no file
system). All side-effects are orchestrated by the service layer.

## Core Domain Models

| Model | Responsibility |
|-------|----------------|
| `City` | Immutable road graph (nodes, edges, stations, zones) |
| `Fleet` | Mutable bike lifecycle (dock, undock, snapshot) |
| `SimulationEngine` | Tick loop, state machine (STOPPED/RUNNING/PAUSED) |
| `Environment` | Weather conditions + special events |
| `RebalanceStrategy` | Pluggable strategy (GreedyThreshold → GA / RL) |

## Data Flow

```
User Input
    │
    ▼
API Endpoint ──► Service ──► Core Model ──► FleetSnapshot
                                       │
                                       ▼
                                    API Response (DTO)
```

## Simulation Tick

Each tick (1 simulated minute by default):

1. Environment drifts (weather, event decay)
2. Demand generates trip requests
3. Trips execute (bikes undock → ride → dock)
4. Rebalance check (every N ticks)
5. Snapshot captured

## Phase Plan

| Phase | Scope |
|-------|-------|
| **Phase 0** | Project skeleton, architecture, CI (✅ done) |
| **Phase 1** | Real map loading (OSM), static bike deployment, basic tests |
| **Phase 2** | Commuter tide demand generation, trip execution |
| **Phase 3** | Rebalancing dispatch, fleet financial model |
| **Phase 4** | Deck.gl visualization, heatmap, OD flow animation |

## Key Design Decisions

1. **Immutable City** — Road network built once; never mutated at runtime
2. **Snapshot pattern** — `FleetSnapshot` for API, mutable `Fleet` for engine
3. **Strategy pattern** — `RebalanceStrategy` interface for pluggable algorithms
4. **No ORM** — In-memory simulation; persistence is out of scope for v1
