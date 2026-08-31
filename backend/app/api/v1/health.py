"""Health Check Endpoint (TICKET-501)."""

from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check():
    """Service health check endpoint."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }
