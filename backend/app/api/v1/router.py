"""API v1 router — simulation endpoints."""

from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/city")
async def get_city():
    return {"message": "not implemented"}


@api_router.get("/fleet")
async def get_fleet():
    return {"message": "not implemented"}


@api_router.post("/simulation/start")
async def start_simulation():
    return {"message": "not implemented"}


@api_router.post("/simulation/pause")
async def pause_simulation():
    return {"message": "not implemented"}


@api_router.get("/simulation/status")
async def simulation_status():
    return {"message": "not implemented"}


@api_router.get("/dashboard/heatmap")
async def heatmap():
    return {"message": "not implemented"}


@api_router.get("/dashboard/flows")
async def od_flows():
    return {"message": "not implemented"}


@api_router.get("/dashboard/stats")
async def dashboard_stats():
    return {"message": "not implemented"}
