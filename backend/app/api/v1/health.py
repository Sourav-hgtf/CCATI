"""Health and Readiness Endpoints with Model Registry & PostgreSQL Connectivity Verification (TICKET-501, TASK 18, TASK 20)."""

from fastapi import APIRouter, Response, status
from backend.app.core.config import settings
from backend.app.db.session import check_db_connected
from ml_engine.registry.model_registry import ModelRegistry

router = APIRouter()


@router.get("/health")
def health_check():
    """Liveness probe: verifies service runtime, database connection, and model integrity status."""
    db_ok, db_status = check_db_connected()
    
    registry = ModelRegistry()
    try:
        active_info = registry.get_active_model_info()
        integrity_ok = registry.verify_integrity(active_info["version"])
        model_name = active_info.get("model_name", "Unknown")
        model_version = active_info.get("version", "Unknown")
    except Exception:
        active_info = {}
        integrity_ok = False
        model_name = "None"
        model_version = "None"

    is_healthy = db_ok and integrity_ok

    return {
        "status": "ok" if is_healthy else "unhealthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "database": db_status,
        "model_active": integrity_ok,
        "model_name": model_name,
        "model_version": model_version,
        "artifact_integrity_verified": integrity_ok,
    }


@router.get("/ready")
def readiness_check(response: Response):
    """Readiness probe: validates database connectivity, storage, and model artifacts."""
    db_ok, db_status = check_db_connected()

    checks = {
        "database": db_ok,
        "model_registry": False,
        "artifact_integrity": False,
    }

    # Check Model Registry & Artifact Integrity
    registry = ModelRegistry()
    try:
        active_info = registry.get_active_model_info()
        checks["model_registry"] = True
        checks["artifact_integrity"] = registry.verify_integrity(active_info["version"])
    except Exception:
        checks["model_registry"] = False
        checks["artifact_integrity"] = False

    all_ready = all(checks.values())
    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
        "database_status": db_status,
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
    }
