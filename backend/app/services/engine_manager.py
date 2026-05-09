"""EngineManager — global singleton owning the single SimulationEngine instance.

All API endpoints that interact with the simulation read/write through
this manager. It lazily initialises the engine on first access and
provides thin wrappers around the engine's lifecycle and query methods.
"""

from __future__ import annotations

from app.core.engine import SimulationEngine, SimState
from app.core.event_bus import EventBus
from app.core.fleet import Bike, Fleet
from app.core.scheduler import GreedyThresholdStrategy
from app.core.weather import Environment
from app.models.schemas import BikeOut, EventOut, FleetOut, SimStatusOut
from app.services.demand_service import RuleBasedDemandService
from app.services.map_service import MapService


class EngineManager:
    """Global singleton managing the single SimulationEngine instance."""

    _instance: EngineManager | None = None

    def __new__(cls) -> EngineManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._engine: SimulationEngine | None = None
            cls._instance._map_service = MapService()
        return cls._instance

    # ── engine lifecycle ──────────────────────────────────────────

    @property
    def engine(self) -> SimulationEngine:
        """Lazily initialise the engine on first access."""
        if self._engine is None:
            self._init_engine()
        return self._engine

    def _init_engine(self, city_name: str = "Beijing") -> None:
        """Construct engine with all required dependencies.

        Phase 4: wires the global EventBus singleton so tick events are
        published for WebSocket broadcaster, AchievementEngine, etc.
        """
        city = self._map_service.load_city(city_name)
        fleet = self._build_starter_fleet()

        # Distribute bikes round-robin across all city stations
        station_ids = list(city.stations.keys())
        if station_ids:
            for i, bike in enumerate(fleet.bikes.values()):
                bike.station_id = station_ids[i % len(station_ids)]

        environment = Environment()
        strategy = GreedyThresholdStrategy()
        trip_generator = RuleBasedDemandService()
        self._engine = SimulationEngine(
            city=city,
            fleet=fleet,
            environment=environment,
            strategy=strategy,
            trip_generator=trip_generator,
            event_bus=EventBus(),
        )

    @staticmethod
    def _build_starter_fleet() -> Fleet:
        """Seed the fleet with starter bikes.

        The caller (_init_engine) is responsible for distributing these
        bikes across city stations after this method returns.
        """
        import random

        random.seed(42)
        fleet = Fleet()
        for i in range(50):
            fleet.add_bike(
                Bike(bike_id=f"bike_{i:04d}", station_id=None)
            )
        return fleet

    def reset_engine(self, city_name: str = "Beijing") -> None:
        """Force-recreate the engine (e.g. when the user wants a fresh sim)."""
        self._engine = None
        self._init_engine(city_name)

    # ── commands ──────────────────────────────────────────────────

    def start(self) -> SimStatusOut:
        """Start the simulation engine. Idempotent if already running."""
        if self.engine.state is not SimState.RUNNING:
            self.engine.start()
        return self.get_status()

    def pause(self) -> SimStatusOut:
        """Pause a running simulation. Auto-starts if stopped."""
        if self.engine.state is SimState.STOPPED:
            self.engine.start()
        self.engine.pause()
        return self.get_status()

    def advance(self, steps: int = 1) -> SimStatusOut:
        """Advance by *steps* ticks. Auto-starts if needed.

        Handles all three non-terminal states:
        - PAUSED  → resume (start) then advance
        - STOPPED → start then advance
        - BANKRUPT → advance (engine allows it, returns last snapshot)
        """
        if self.engine.state is SimState.PAUSED:
            self.engine.start()  # resume from pause
        elif self.engine.state is SimState.STOPPED:
            self.engine.start()
        # RUNNING and BANKRUPT fall through directly
        self.engine.advance(steps)
        return self.get_status()

    # ── queries ───────────────────────────────────────────────────

    def get_status(self) -> SimStatusOut:
        """Return current simulation status from engine state."""
        state_map = {
            SimState.STOPPED: "stopped",
            SimState.RUNNING: "running",
            SimState.PAUSED: "paused",
            SimState.BANKRUPT: "bankrupt",
        }
        return SimStatusOut(
            tick=self.engine.tick,
            state=state_map.get(self.engine.state, "stopped"),
            time_of_day=self.engine.time_of_day(),
        )

    def get_fleet(self) -> FleetOut:
        """Return current fleet snapshot as FleetOut."""
        snap = self.engine.fleet.snapshot()
        bikes = [
            BikeOut(
                bike_id=b.bike_id,
                status=b.status.name.lower(),
                station_id=b.station_id,
                lat=b.position.lat if b.position else None,
                lng=b.position.lng if b.position else None,
            )
            for b in snap.bikes
        ]
        return FleetOut(
            total_bikes=snap.total_bikes,
            active_rides=snap.total.get("IN_USE", 0),
            lost_bikes=snap.total.get("LOST", 0),
            bikes=bikes,
        )

    def get_bike(self, bike_id: str) -> BikeOut | None:
        """Look up a single bike by ID. Returns None if not found."""
        bike = self.engine.fleet.get_bike(bike_id)
        if bike is None:
            return None
        return BikeOut(
            bike_id=bike.bike_id,
            status=bike.status.name.lower(),
            station_id=bike.station_id,
            lat=bike.position.lat if bike.position else None,
            lng=bike.position.lng if bike.position else None,
        )

    def get_events(self) -> list[EventOut]:
        """Return active special events from the engine's environment."""
        return [
            EventOut(
                event_id=ev.event_id,
                name=ev.name,
                zone_id=ev.station_id,
                start_tick=0,  # SpecialEvent doesn't track start tick yet
                duration_ticks=ev.duration_ticks,
                demand_multiplier=ev.demand_multiplier,
            )
            for ev in self.engine.environment.events.values()
        ]
