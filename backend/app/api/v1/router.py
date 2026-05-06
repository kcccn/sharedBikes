"""API v1 router — simulation, fleet, city, and dashboard endpoints."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


# ── City ────────────────────────────────────────────────

@router.get("/city")
async def get_city():
    """Return city metadata (node/edge/station counts)."""
    return {"message": "not implemented", "node_count": 0, "edge_count": 0, "station_count": 0}


@router.get("/city/stations")
async def list_stations():
    """List all docking stations."""
    return {"message": "not implemented", "stations": []}


@router.get("/city/stations/{station_id}")
async def get_station(station_id: str):
    """Get details for a single station."""
    return {"message": "not implemented", "station_id": station_id}


# ── Fleet ───────────────────────────────────────────────

@router.get("/fleet")
async def get_fleet():
    """Return current fleet snapshot."""
    return {"message": "not implemented", "total_bikes": 0, "docked": 0, "in_use": 0}


@router.get("/fleet/bikes/{bike_id}")
async def get_bike(bike_id: str):
    """Get details for a single bike."""
    return {"message": "not implemented", "bike_id": bike_id}


# ── Simulation ──────────────────────────────────────────

@router.post("/simulation/start")
async def start_simulation():
    """Start or restart the simulation engine."""
    return {"message": "not implemented", "state": "stopped"}


@router.post("/simulation/pause")
async def pause_simulation():
    """Pause the running simulation."""
    return {"message": "not implemented", "state": "paused"}


@router.post("/simulation/resume")
async def resume_simulation():
    """Resume a paused simulation."""
    return {"message": "not implemented", "state": "running"}


@router.post("/simulation/stop")
async def stop_simulation():
    """Stop the simulation (keep state)."""
    return {"message": "not implemented", "state": "stopped"}


@router.post("/simulation/reset")
async def reset_simulation():
    """Reset simulation to initial state."""
    return {"message": "not implemented", "state": "stopped"}


@router.get("/simulation/status")
async def simulation_status():
    """Get current simulation tick, time, and state."""
    return {
        "message": "not implemented",
        "state": "stopped",
        "tick": 0,
        "time_of_day": "00:00",
    }


# ── Dashboard ───────────────────────────────────────────

@router.get("/dashboard/heatmap")
async def get_heatmap():
    """Real-time supply/demand heatmap data."""
    return {"message": "not implemented", "cells": []}


@router.get("/dashboard/flows")
async def get_flows():
    """OD flow lines for trip visualisation."""
    return {"message": "not implemented", "flows": []}
