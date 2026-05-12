"""City configuration model — describes how a city is loaded and simulated.

This is a pure-core dataclass (no I/O, no framework dependency) that
serves as the contract between the config file format and the loader.

Note: OSM data source configuration has been removed. All cities are
now generated procedurally (ProceduralCityGenerator). The config file
retains simulation tuning parameters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class StationGenerationConfig:
    """Parameters for auto-generating stations on the road network."""

    enabled: bool = True
    min_distance_km: float = 0.3
    min_capacity: int = 10
    max_capacity: int = 50
    max_stations: int | None = None


@dataclass(frozen=True)
class ProceduralConfig:
    """Procedural generation parameters for the city generator."""

    grid_rows: int = 35
    grid_cols: int = 35
    spacing: float = 1.0
    jitter: float = 0.1


@dataclass(frozen=True)
class CityConfig:
    """Complete configuration for loading and simulating a city."""

    # ── Identity ────────────────────────────────────────
    city_id: str
    display_name: str = ""
    country: str = ""
    timezone: str = "UTC"

    # ── Procedural generation ───────────────────────────
    procedural: ProceduralConfig = field(default_factory=ProceduralConfig)

    # ── Simulation defaults ─────────────────────────────
    default_station_capacity: int = 30
    initial_bikes_per_station: int = 10
    ticks_per_day: int = 1440

    # ── Station placement ───────────────────────────────
    station_generation: StationGenerationConfig = field(
        default_factory=StationGenerationConfig
    )

    # ── Fleet ───────────────────────────────────────────
    total_bikes: int = 500

    # ── Demand ──────────────────────────────────────────
    peak_hour_multiplier: float = 3.0
    off_peak_multiplier: float = 0.3

    # ── Zones (optional override) ───────────────────────
    zone_configs: tuple[dict, ...] = ()
    """Each dict: {zone_id, name, polygon: [{x, y}, ...]}"""
