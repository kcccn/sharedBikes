"""SQLAlchemy ORM models for CityBike-Sim.

These correspond closely to the Pydantic domain models in backend/models.py
but include PostGIS geometry columns for spatial queries.
"""

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class BikeModel(Base):
    __tablename__ = "bikes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default="available")
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    last_ride_at = Column(DateTime(timezone=True), nullable=True)
    total_rides: Mapped[int] = mapped_column(Integer, default=0)
    total_distance_km: Mapped[float] = mapped_column(Float, default=0.0)


class ParkingPointModel(Base):
    __tablename__ = "parking_points"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=30)
    current_count: Mapped[int] = mapped_column(Integer, default=0)


class TripModel(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    bike_id: Mapped[str] = mapped_column(ForeignKey("bikes.id"))
    user_id: Mapped[str] = mapped_column(String(32))
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    start_point = Column(Geometry("POINT", srid=4326), nullable=False)
    end_point = Column(Geometry("POINT", srid=4326), nullable=True)
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    fare: Mapped[float | None] = mapped_column(Float, nullable=True)

    bike = relationship("BikeModel", backref="trips")
