"""Core domain models for CityBike-Sim."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Point(BaseModel):
    """Geographic point with latitude/longitude."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    lng: float = Field(..., ge=-180, le=180, description="Longitude in degrees")


class BikeStatus(str, Enum):
    """Operational status of a bike."""
    available = "available"       # 可用 — parked and ready to ride
    in_use = "in_use"            # 使用中 — being ridden
    damaged = "damaged"          # 损坏 — needs maintenance
    lost = "lost"                # 丢失 — last known location only
    rebalancing = "rebalancing"  # 调度中 — being relocated by fleet


class Bike(BaseModel):
    """A single shared bike in the fleet."""
    id: str
    status: BikeStatus = BikeStatus.available
    location: Point
    last_ride_at: Optional[datetime] = None
    total_rides: int = 0
    total_distance_km: float = 0.0


class ParkingPoint(BaseModel):
    """Recommended parking point (P点) near transit hubs."""
    id: str
    location: Point
    name: str
    capacity: int = Field(default=30, ge=1, description="Max bikes this point can hold")
    current_count: int = 0


class NoParkingZone(BaseModel):
    """Geo-fenced area where parking is prohibited."""
    id: str
    name: str
    boundary: list[Point]  # Polygon vertices defining the zone
    fine_per_bike: float = Field(default=50.0, ge=0)


class FleetVehicleType(str, Enum):
    """Types of rebalancing vehicles."""
    tricycle = "tricycle"       # 三轮车 — nimble, small capacity
    van = "van"                 # 厢式货车 — large capacity, slower


class FleetVehicle(BaseModel):
    """A vehicle used for bike rebalancing."""
    id: str
    vehicle_type: FleetVehicleType
    capacity: int
    current_load: int = 0
    location: Point
    driver: Optional[str] = None


class Trip(BaseModel):
    """A completed bike trip / ride order."""
    id: str
    bike_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    start_point: Point
    end_point: Optional[Point] = None
    distance_km: Optional[float] = None
    fare: Optional[float] = None


class WeatherCondition(str, Enum):
    """Weather conditions affecting demand."""
    clear = "clear"
    cloudy = "cloudy"
    rainy = "rainy"
    storm = "storm"
    typhoon = "typhoon"
    snowy = "snowy"


class GameState(BaseModel):
    """Top-level simulation game state."""
    game_id: str
    timestamp: datetime
    city_name: str
    day: int = 1
    hour: int = 8
    weather: WeatherCondition = WeatherCondition.clear
    temperature_c: float = 25.0
    budget: float = 100_000.0
    daily_revenue: float = 0.0
    total_bikes: int = 0
    active_trips: int = 0
