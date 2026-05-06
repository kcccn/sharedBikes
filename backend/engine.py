"""Simulation engine — the heart of CityBike-Sim.

Manages the game loop: tick-based time progression, demand generation,
rebalancing dispatch, and financial settlement.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable

from backend.models import (
    Bike,
    FleetVehicle,
    FleetVehicleType,
    GameState,
    ParkingPoint,
    Point,
    WeatherCondition,
)


@dataclass
class SimulationConfig:
    """Configuration parameters for a simulation run."""
    city_name: str = "unknown"
    sim_speed: int = 60  # 1 real second = N game minutes
    tick_interval_s: float = 1.0
    total_bikes: int = 1000
    total_parking_points: int = 50
    no_parking_zones: list[dict] = field(default_factory=list)


class SimulationEngine:
    """Main simulation loop orchestrator."""

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.state = GameState(
            game_id="sim-001",
            timestamp=datetime.now(),
            city_name=config.city_name,
        )
        self.bikes: dict[str, Bike] = {}
        self.vehicles: dict[str, FleetVehicle] = {}
        self.parking_points: dict[str, ParkingPoint] = {}
        self._tick = 0

    def initialize(self) -> None:
        """Seed the simulation with initial assets."""
        # TODO: load real OSM city data and generate assets
        for i in range(self.config.total_bikes):
            bike = Bike(
                id=f"bike-{i:06d}",
                location=Point(
                    lat=random.uniform(30.0, 40.0),
                    lng=random.uniform(110.0, 120.0),
                ),
            )
            self.bikes[bike.id] = bike

        self.state.total_bikes = len(self.bikes)

        # Seed a few fleet vehicles
        for vid in range(5):
            v = FleetVehicle(
                id=f"vehicle-{vid:03d}",
                vehicle_type=random.choice(list(FleetVehicleType)),
                capacity=30 if vid < 3 else 80,
                location=Point(lat=35.0, lng=115.0),
            )
            self.vehicles[v.id] = v

    def tick(self) -> GameState:
        """Advance the simulation by one tick."""
        self._tick += 1

        # TODO: demand generation, trip completion, rebalancing AI
        if self._tick % 60 == 0:
            self.state.hour = (self.state.hour + 1) % 24
            if self.state.hour == 0:
                self.state.day += 1
                self.state.daily_revenue = 0.0

        self.state.timestamp = datetime.now()
        self.state.active_trips = random.randint(10, 200)
        self.state.daily_revenue += random.uniform(50, 500)

        return self.state

    def run(self, steps: int, on_step: Callable[[GameState], None]) -> None:
        """Run the simulation for a given number of steps."""
        for _ in range(steps):
            self.tick()
            on_step(self.state)
