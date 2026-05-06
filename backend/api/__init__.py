"""API routers for CityBike-Sim."""

from fastapi import APIRouter

from backend.api.health import router as health_router

router = APIRouter()
router.include_router(health_router)
