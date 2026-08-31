"""Health and Readiness Endpoints with Model Registry Integrity Verification (TICKET-501, TASK 3, TASK 10)."""

import sqlite3
from fastapi import APIRouter, Response, status
from backend.app.core.config import settings
from ml_engine.registry.model_registry import ModelRegistry

router = APIRouter()


@router.get("/health")
def health_check():
    """Liveness probe: verifies service runtime and model integrity status."""
    registry = ModelRegistry()
    try:
        active_info = registry.get_active_model_info()
        integrity_ok = registry.verify_integrity(active_info["version"])
        model_name = active_info.get("model_name", "Unknown")
        model_version = active_info.get("version", "Unknown")
        is_healthy = integrity_ok
    except Exception:
        active_info = {}
        integrity_ok = False
        model_name = "None"
        model_version = "None"
        is_healthy = False

    return {
        "status": "ok" if is_healthy else "unhealthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "model_active": is_healthy,
        "model_name": model_name,
        "model_version": model_version,
        "artifact_integrity_verified": integrity_ok,
    }


@router.get("/ready")
def readiness_check(response: Response):
    """Readiness probe: validates database connectivity, storage, and model artifacts."""
    checks = {
        "database": False,
        "model_registry": False,
        "artifact_integrity": False,
    }

    # 1. Check Database connectivity
    try:
        conn = sqlite3.connect(settings.DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        checks["database"] = True
    except Exception:
        checks["database"] = False

    # 2. Check Model Registry & Artifact Integrity
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
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
    }
