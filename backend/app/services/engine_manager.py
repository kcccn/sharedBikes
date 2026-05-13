"""EngineManager — global singleton owning the single SimulationEngine instance.

All API endpoints that interact with the simulation read/write through
this manager. It lazily initialises the engine on first access and
provides thin wrappers around the engine's lifecycle and query methods.

Phase C: EngineManager now also owns a GameSession instance, drains the
player command queue before each advance(), and exposes session info
for WS tick messages and REST endpoints.
"""

from __future__ import annotations

from typing import Any

from app.core.achievement import AchievementEngine, BUILTIN_ACHIEVEMENTS
from app.core.dispatch_cost import DispatchBudget
from app.core.engine import SimulationEngine, SimState
from app.core.event_bus import EventBus
from app.core.fleet import Bike, Fleet
from app.core.satisfaction import SatisfactionTracker
from app.core.scheduler import CostAwareRebalanceStrategy, GreedyThresholdStrategy
from app.core.weather import Environment
from app.models.npc import NpcPopulation
from app.models.schemas import BikeOut, EventOut, FleetOut, SimStatusOut
from app.services.command_handler import CommandHandler
from app.services.demand_service import CommuteDemandService, RuleBasedDemandService
from app.services.game_session import (
    CommandAction,
    GameSession,
    DailyReport as SessionDailyReport,
)
from app.services.leaderboard_service import (
    StationStatsSummary,
    StationStatsTracker,
)
from app.services.map_service import MapService


class EngineManager:
    """Global singleton managing the single SimulationEngine instance."""

    _instance: EngineManager | None = None

    def __new__(cls) -> EngineManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._engine: SimulationEngine | None = None
            cls._instance._station_stats_tracker: StationStatsTracker | None = None
            cls._instance._map_service = MapService()
            # Phase C: GameSession
            cls._instance._session: GameSession | None = None
            # Cached tick data for WS consumption
            cls._instance._last_tick_balance: float = 0.0
            cls._instance._last_daily_report: SessionDailyReport | None = None
        return cls._instance

    # ── engine lifecycle ──────────────────────────────────────────

    @property
    def engine(self) -> SimulationEngine:
        """Lazily initialise the engine on first access."""
        if self._engine is None:
            self._init_engine()
        return self._engine

    @property
    def session(self) -> GameSession:
        """Lazily initialise the GameSession on first access."""
        if self._session is None:
            self._session = GameSession()
        return self._session

    def _init_engine(self, city_name: str = "default") -> None:
        """Construct engine with all required dependencies.

        Phase 4: wires the global EventBus singleton so tick events are
        published for WebSocket broadcaster, AchievementEngine, etc.
        Phase C: creates a fresh GameSession.
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
        engine_event_bus = EventBus()
        self._engine = SimulationEngine(
            city=city,
            fleet=fleet,
            environment=environment,
            strategy=strategy,
            trip_generator=trip_generator,
            event_bus=engine_event_bus,
        )

        # Wire AchievementEngine (Phase 6 P0)
        achievement_engine = AchievementEngine(engine=self._engine)
        achievement_engine.register(*BUILTIN_ACHIEVEMENTS)

        # Wire StationStatsTracker (Phase 6 P1)
        self._station_stats_tracker = StationStatsTracker()

        # Phase C: fresh GameSession
        self._session = GameSession()
        self._last_tick_balance = 0.0
        self._last_daily_report = None

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

    @property
    def station_stats_tracker(self) -> StationStatsTracker:
        """Lazily initialised StationStatsTracker (wired in _init_engine)."""
        if self._station_stats_tracker is None:
            self._init_engine()
        assert self._station_stats_tracker is not None
        return self._station_stats_tracker

    def reset_engine(self, city_name: str = "default") -> None:
        """Force-recreate the engine (e.g. when the user wants a fresh sim)."""
        self._engine = None
        self._station_stats_tracker = None
        self._init_engine(city_name)

    # ── Phase C: session API ──────────────────────────────────────

    def get_session_summary(self) -> dict[str, Any]:
        """Return current GameSession summary for REST endpoint."""
        return self.session.to_dict()

    def reset_session(self) -> dict[str, Any]:
        """Reset GameSession (new balance, clear history)."""
        self._session = GameSession()
        return self._session.to_dict()

    def enqueue_command(
        self,
        action: str,
        payload: dict[str, Any],
        tick: int,
    ) -> str | None:
        """Validate and enqueue a player command.

        Returns command_id on success, None on validation failure.
        The actual validation message can be fetched from the
        CommandHandler's validate() return.
        """
        try:
            cmd_action = CommandAction(action)
        except ValueError:
            return None

        # Validate first
        validation = CommandHandler.validate(cmd_action, payload, self.session, self.engine)
        if not validation.success:
            return None

        # Enqueue
        return self.session.enqueue(cmd_action, payload, tick)

    # ── command execution helpers ──────────────────────────────────

    def _drain_commands(self, tick: int) -> None:
        """Execute all pending player commands before a simulation step."""
        pending = self.session.drain_queue()
        if not pending:
            return

        handler = CommandHandler()
        for envelope in pending:
            # Re-validate (state may have changed since enqueue)
            validation = handler.validate(
                envelope.action, envelope.payload, self.session, self.engine
            )
            if not validation.success:
                self.session.record_result(validation)
                continue

            # Execute
            result = handler.execute(
                envelope.action,
                envelope.payload,
                self.session,
                self.engine,
                envelope.command_id,
                tick,
            )
            self.session.record_result(result)

    def _capture_tick_state(self) -> None:
        """Capture balance and daily report after engine advance."""
        self._last_tick_balance = self.session.player_balance

        # Check if a new daily report was generated by the engine
        engine_reports = self.engine.daily_reports
        if engine_reports:
            latest = engine_reports[-1]
            report = SessionDailyReport(
                day=latest.day,
                revenue_today=latest.revenue_today,
                costs_today=latest.costs_today,
                profit_today=latest.profit_today,
                cumulative_balance=latest.cumulative_balance,
                alert=latest.alert,
            )
            self._last_daily_report = report
            self.session.set_last_report(report)

    # ── public tick data access (for WS handler) ──────────────────

    @property
    def last_tick_balance(self) -> float:
        """Player balance after the most recent tick."""
        return self._last_tick_balance

    @property
    def last_daily_report_dict(self) -> dict[str, Any] | None:
        """Latest daily report as a dict (or None if no report yet)."""
        if self._last_daily_report is None:
            return None
        r = self._last_daily_report
        return {
            "day": r.day,
            "revenue_today": round(r.revenue_today, 2),
            "costs_today": round(r.costs_today, 2),
            "profit_today": round(r.profit_today, 2),
            "cumulative_balance": round(r.cumulative_balance, 2),
            "alert": r.alert,
        }

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

        Phase C: drains pending player commands before each advance,
        then captures tick state (balance, daily report) after.
        """
        if self.engine.state is SimState.PAUSED:
            self.engine.start()  # resume from pause
        elif self.engine.state is SimState.STOPPED:
            self.engine.start()
        # RUNNING and BANKRUPT fall through directly

        # Phase C: drain player commands before simulating
        self._drain_commands(self.engine.tick)

        # Advance the simulation
        self.engine.advance(steps)

        # Phase C: capture post-tick state
        self._capture_tick_state()

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
                x=b.position.x if b.position else None,
                y=b.position.y if b.position else None,
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
            x=bike.position.x if bike.position else None,
            y=bike.position.y if bike.position else None,
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
