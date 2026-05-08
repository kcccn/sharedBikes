"""Trip executor — manages trip lifecycle and bike assignment.

Phase 2 uses a *completed_tick* pattern: each trip's expected completion
tick is pre-computed from distance and average speed. No tick-by-tick
state machine is needed.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from app.core.finance import RevenueCategory
from app.core.fleet import Fleet

# Re-export for convenience; TripRequest is the demand-service type
from app.services.demand_service import TripRequest as TripRequest


@dataclass
class ActiveTrip:
    """A trip that has started and will complete at *completed_tick*."""

    trip: TripRequest
    started_tick: int
    completed_tick: int
    distance_km: float

    @property
    def trip_id(self) -> str:
        return f"trip-{self.started_tick}-{self.trip.from_station}-{self.trip.to_station}"


# Average cycling speed in km/h — used to estimate trip duration
# This is a configurable tuning parameter
_AVG_SPEED_KMH = 15.0


class TripExecutor:
    """Manages active trips and advances them each tick.

    On each ``advance()`` call:
    1. Assigns bikes to new trips (undocks from fleet)
    2. Returns trips whose ``completed_tick == current_tick``
    """

    def __init__(self, fleet: Fleet, avg_speed_kmh: float = _AVG_SPEED_KMH) -> None:
        self._fleet = fleet
        self._avg_speed_kmh = avg_speed_kmh
        self._active_trips: list[ActiveTrip] = []

    def advance(
        self,
        current_tick: int,
        new_trip_requests: list[TripRequest],
        distances: dict[tuple[str, str], float],
    ) -> list[ActiveTrip]:
        """Advance the trip executor by one tick.

        Args:
            current_tick: The current simulation tick.
            new_trip_requests: Trip requests generated for this tick.
            distances: Pre-computed distance cache {(from, to): km}.

        Returns:
            List of ``ActiveTrip`` that completed on *current_tick*.
        """
        # 1. Start new trips — assign bikes
        for req in new_trip_requests:
            if req.bike_id is not None:
                # Already has a bike assigned (e.g., from a re-queue)
                continue

            bike = self._assign_bike(req.from_station)
            if bike is None:
                continue  # no available bike at this station — trip lost

            bike.undock()
            req.bike_id = bike.bike_id

            # Calculate distance
            distance = distances.get(
                (req.from_station, req.to_station),
                # Fallback: assume 2 km if unknown
                2.0,
            )

            # Estimate completion tick
            duration_ticks = max(1, math.ceil(
                distance / self._avg_speed_kmh * 60  # duration in minutes = ticks
            ))

            active = ActiveTrip(
                trip=req,
                started_tick=current_tick,
                completed_tick=current_tick + duration_ticks,
                distance_km=distance,
            )
            self._active_trips.append(active)

        # 2. Collect completed trips
        completed: list[ActiveTrip] = []
        remaining: list[ActiveTrip] = []
        for at in self._active_trips:
            if at.completed_tick <= current_tick:
                completed.append(at)
                # Dock the bike at destination
                bike = self._fleet.get_bike(at.trip.bike_id or "")
                if bike is not None:
                    bike.dock(at.trip.to_station)
                    bike.total_rides += 1
                    bike.total_distance_km += at.distance_km
            else:
                remaining.append(at)
        self._active_trips = remaining

        return completed

    @property
    def active_trip_count(self) -> int:
        """Number of currently active (in-progress) trips."""
        return len(self._active_trips)

    # ── private helpers ──────────────────────────────────────────

    def _assign_bike(self, station_id: str) -> object | None:
        """Find an AVAILABLE bike at *station_id* and return it."""
        from app.core.fleet import Bike, BikeStatus

        bikes = [
            b for b in self._fleet.bikes.values()
            if b.station_id == station_id and b.status == BikeStatus.AVAILABLE
        ]
        if not bikes:
            return None
        return random.choice(bikes)
