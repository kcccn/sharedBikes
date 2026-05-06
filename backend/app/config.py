"""Centralized configuration — single source of truth for all tunables."""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SimulationConfig:
    """Game-world simulation parameters."""

    # ── Time ──────────────────────────────────────────────
    tick_interval_sec: float = 1.0          # Real seconds per simulation tick
    ticks_per_day: int = 1440               # 1 tick = 1 simulated minute
    speed_multiplier: float = 60.0          # 1 real sec = 1 simulated hour by default

    # ── Fleet ─────────────────────────────────────────────
    initial_bikes_per_station: int = 10
    max_bikes_per_station: int = 50
    bike_speed_kmh: float = 15.0
    bike_range_km: float = 5.0

    # ── Demand ────────────────────────────────────────────
    peak_multiplier: float = 3.0
    off_peak_multiplier: float = 0.3
    commuter_radius_km: float = 3.0

    # ── Rebalancing ───────────────────────────────────────
    rebalance_trigger_ratio: float = 0.2    # Trigger rebalance when station <20% or >80% full
    truck_capacity: int = 40
    trike_capacity: int = 12


@dataclass(frozen=True)
class AppConfig:
    """Application-level settings."""

    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    data_dir: Path = Path(os.getenv("CITYBIKE_DATA_DIR", "data"))
    osm_cache_dir: Path = Path(os.getenv("CITYBIKE_OSM_CACHE", "data/osm_cache"))

    simulation: SimulationConfig = field(default_factory=SimulationConfig)


# Global singleton — thread-safe via double-checked locking.
_config: AppConfig | None = None
_config_lock = threading.Lock()


def get_config() -> AppConfig:
    global _config
    if _config is None:
        with _config_lock:
            if _config is None:
                _config = AppConfig(
                    debug=os.getenv("CITYBIKE_DEBUG", "0") == "1",
                )
    return _config
