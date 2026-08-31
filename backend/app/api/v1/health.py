"""Health Check Endpoint with Model Registry Integrity Verification (TICKET-501, TASK 3)."""

from fastapi import APIRouter
from backend.app.core.config import settings
from ml_engine.registry.model_registry import ModelRegistry

router = APIRouter()


@router.get("/health")
def health_check():
    """Service health check endpoint with active model & artifact integrity verification."""
    registry = ModelRegistry()
    try:
        active_info = registry.get_active_model_info()
        integrity_ok = registry.verify_integrity(active_info["version"])
        model_name = active_info.get("model_name", "Unknown")
        model_version = active_info.get("version", "Unknown")
        is_healthy = integrity_ok
    except Exception as e:
        active_info = {}
        integrity_ok = False
        model_name = "None"
        model_version = "None"
        is_healthy = False

    return {
        "status": "ok" if is_healthy else "unhealthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "model_active": is_healthy,
        "model_name": model_name,
        "model_version": model_version,
        "artifact_integrity_verified": integrity_ok,
    }
