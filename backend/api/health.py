"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check returning service status."""
    return {"status": "ok", "service": "citybike-sim"}
