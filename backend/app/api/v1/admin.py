"""Admin Endpoints (TASK 17 - Production User Management & RBAC Administration, TASK-21 - ML Training).

Provides:
  - GET  /admin/audit-logs:                   Retrieve security audit logs (Admin only)
  - GET  /admin/users:                         List all system users with roles and status (Admin only)
  - POST /admin/users:                         Create a new system user with password validation (Admin only)
  - PATCH /admin/users/{id}/role:              Update a user's role with admin demotion guard (Admin only)
  - PATCH /admin/users/{id}/status:            Activate/Deactivate user with admin lockout guard (Admin only)
  - POST /admin/training/kaggle-ingest:        Ingest Cell2Cell Kaggle CSV into the ML pipeline (Admin only)
  - POST /admin/training/retrain:              Trigger model retraining with configurable data source (Admin only)
  - GET  /admin/training/dataset-registry:     List all registered datasets with SHA-256 checksums (Admin only)
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.core.audit import get_audit_logs, log_audit_event
from backend.app.core.crypto import get_password_hash, validate_password_strength
from backend.app.core.rate_limiter import rate_limit_admin
from backend.app.core.rbac import (
    ALL_ROLES,
    ROLE_ADMIN,
    UserContext,
    require_roles,
)
from backend.app.db.session import get_db
from backend.app.db.repositories.user_repo import UserRepository
from backend.app.schemas.auth import (
    CreateUserRequest,
    UpdateUserRoleRequest,
    UpdateUserStatusRequest,
    UserResponse,
)

router = APIRouter()


@router.get("/admin/audit-logs", dependencies=[Depends(rate_limit_admin)])
def get_system_audit_logs(
    limit: int = 100,
    current_user: UserContext = Depends(require_roles([ROLE_ADMIN])),
):
    """Retrieve security and business audit logs (Admin only)."""
    logs = get_audit_logs(limit=limit)
    return {"total": len(logs), "logs": logs}


@router.get("/admin/users", response_model=dict, dependencies=[Depends(rate_limit_admin)])
def list_system_users(
    current_user: UserContext = Depends(require_roles([ROLE_ADMIN])),
    db: Session = Depends(get_db),
):
    """List all registered system users and their active role assignments (Admin only)."""
    repo = UserRepository(db)
    users = repo.get_all()
    user_list = [
        UserResponse(
            user_id=u.id,
            email=u.email,
            username=u.username,
            name=u.full_name,
            role=u.role,
            status="Active" if u.is_active else "Inactive",
            is_active=u.is_active,
            created_at=u.created_at.isoformat() if u.created_at else None,
            last_login_at=u.last_login_at.isoformat() if u.last_login_at else None,
        ).model_dump()
        for u in users
    ]
    return {"total": len(user_list), "users": user_list}


@router.post("/admin/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit_admin)])
def create_system_user(
    payload: CreateUserRequest,
    request: Request,
    current_user: UserContext = Depends(require_roles([ROLE_ADMIN])),
    db: Session = Depends(get_db),
):
    """Create a new system user with role assignment (Admin only)."""
    repo = UserRepository(db)
    
    # Check for existing email or username
    if repo.get_by_email(payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists.",
        )
    if repo.get_by_username(payload.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this username already exists.",
        )

    # Validate role
    if payload.role not in ALL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{payload.role}'. Must be one of: {ALL_ROLES}",
        )

    # Validate password complexity
    valid_pw, pw_err = validate_password_strength(payload.password)
    if not valid_pw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=pw_err,
        )

    user_id = f"usr-{uuid.uuid4().hex[:8]}"
    password_hash = get_password_hash(payload.password)
    new_user = repo.create_user(
        user_id=user_id,
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        password_hash=password_hash,
        role=payload.role,
        is_active=True,
    )

    log_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="USER_CREATED",
        target_resource=f"user:{new_user.id}",
        details=f"Created user {new_user.email} with role {new_user.role}",
        request_id=request.headers.get("X-Request-ID"),
        event_type="USER_CREATED",
        status="SUCCESS",
    )

    return UserResponse(
        user_id=new_user.id,
        email=new_user.email,
        username=new_user.username,
        name=new_user.full_name,
        role=new_user.role,
        status="Active" if new_user.is_active else "Inactive",
        is_active=new_user.is_active,
        created_at=new_user.created_at.isoformat() if new_user.created_at else None,
        last_login_at=None,
    )


@router.patch("/admin/users/{user_id}/role", response_model=UserResponse, dependencies=[Depends(rate_limit_admin)])
def update_user_role(
    user_id: str,
    payload: UpdateUserRoleRequest,
    request: Request,
    current_user: UserContext = Depends(require_roles([ROLE_ADMIN])),
    db: Session = Depends(get_db),
):
    """Update a user's role assignment (Admin only). Guard against demoting last active Admin."""
    repo = UserRepository(db)
    target_user = repo.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found.",
        )

    if payload.role not in ALL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{payload.role}'. Must be one of: {ALL_ROLES}",
        )

    # Protect against removing/demoting the last active administrator
    if target_user.role == ROLE_ADMIN and payload.role != ROLE_ADMIN:
        active_admins = repo.count_active_admins()
        if active_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last active Administrator in the system.",
            )

    old_role = target_user.role
    updated = repo.update_role(target_user, payload.role)

    log_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="USER_ROLE_UPDATED",
        target_resource=f"user:{user_id}",
        details=f"Updated role for {updated.email} from {old_role} to {payload.role}",
        request_id=request.headers.get("X-Request-ID"),
        event_type="USER_ROLE_UPDATED",
        status="SUCCESS",
    )

    return UserResponse(
        user_id=updated.id,
        email=updated.email,
        username=updated.username,
        name=updated.full_name,
        role=updated.role,
        status="Active" if updated.is_active else "Inactive",
        is_active=updated.is_active,
        created_at=updated.created_at.isoformat() if updated.created_at else None,
        last_login_at=updated.last_login_at.isoformat() if updated.last_login_at else None,
    )


@router.patch("/admin/users/{user_id}/status", response_model=UserResponse, dependencies=[Depends(rate_limit_admin)])
def update_user_status(
    user_id: str,
    payload: UpdateUserStatusRequest,
    request: Request,
    current_user: UserContext = Depends(require_roles([ROLE_ADMIN])),
    db: Session = Depends(get_db),
):
    """Enable or disable a user account (Admin only). Guard against deactivating last active Admin."""
    repo = UserRepository(db)
    target_user = repo.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found.",
        )

    # Protect against deactivating the last active administrator
    if target_user.role == ROLE_ADMIN and not payload.is_active:
        active_admins = repo.count_active_admins()
        if active_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the last active Administrator in the system.",
            )

    updated = repo.update_status(target_user, payload.is_active)

    log_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="USER_STATUS_UPDATED",
        target_resource=f"user:{user_id}",
        details=f"Updated active status for {updated.email} to {payload.is_active}",
        request_id=request.headers.get("X-Request-ID"),
        event_type="USER_STATUS_UPDATED",
        status="SUCCESS",
    )

    return UserResponse(
        user_id=updated.id,
        email=updated.email,
        username=updated.username,
        name=updated.full_name,
        role=updated.role,
        status="Active" if updated.is_active else "Inactive",
        is_active=updated.is_active,
        created_at=updated.created_at.isoformat() if updated.created_at else None,
        last_login_at=updated.last_login_at.isoformat() if updated.last_login_at else None,
    )


# ──────────────────────────────────────────────────────────────────────────────
# TASK-21: ML Training Administration Endpoints
# ──────────────────────────────────────────────────────────────────────────────

from pathlib import Path
from pydantic import BaseModel, Field


class KaggleIngestRequest(BaseModel):
    """Request body for the Kaggle CSV ingestion endpoint."""
    kaggle_csv_path: str = Field(
        default="data/raw/cell2cell_churn.csv",
        description="Path to the Cell2Cell Kaggle CSV file (relative to project root or absolute).",
        examples=["data/raw/cell2cell_churn.csv"],
    )
    schedule_type: str = Field(
        default="on_demand",
        description="Audit label for this ingestion run.",
    )


class TelcoIngestRequest(BaseModel):
    """Request body for the Telco CSV ingestion endpoint."""
    telco_csv_path: str = Field(
        default="data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv",
        description="Path to the IBM Telco CSV file.",
        examples=["data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv"],
    )
    schedule_type: str = Field(
        default="on_demand",
        description="Audit label for this ingestion run.",
    )


class RetrainRequest(BaseModel):
    """Request body for the model retraining endpoint."""
    data_source: str = Field(
        default="synthetic",
        description="Dataset to train on: 'synthetic', 'kaggle', or 'telco'.",
        examples=["synthetic", "kaggle", "telco"],
    )
    promote_best: bool = Field(
        default=True,
        description="Whether to automatically promote the best model to production.",
    )


@router.post("/admin/training/kaggle-ingest", dependencies=[Depends(rate_limit_admin)])
def trigger_kaggle_ingestion(
    payload: KaggleIngestRequest,
    request: Request,
    current_user: UserContext = Depends(require_roles([ROLE_ADMIN])),
):
    """Ingest the Cell2Cell Kaggle CSV through the canonical ML pipeline (Admin only).

    - Validates Cell2Cell schema
    - Maps columns to canonical feature schema
    - Runs DQ checks, imputation, and feature engineering
    - Saves to ``data/processed/kaggle_features.parquet`` and ``customer_features.parquet``
    - Registers dataset with SHA-256 checksum in ``data/raw/dataset_registry.json``
    - Persists ingested customers to PostgreSQL

    The raw Kaggle CSV is **never overwritten**.
    """
    from ml_engine.pipelines.ingestion import run_batch_ingestion

    csv_path = Path(payload.kaggle_csv_path)

    try:
        summary = run_batch_ingestion(
            source="kaggle",
            raw_kaggle_path=csv_path,
            db_path=None,  # Use PostgreSQL in production
            schedule_type=payload.schedule_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Kaggle ingestion failed: {exc}",
        )

    log_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="KAGGLE_INGEST",
        target_resource=f"file:{payload.kaggle_csv_path}",
        details=(
            f"Ingested {summary.get('rows_ingested', 0):,} rows from "
            f"'{payload.kaggle_csv_path}'. Status: {summary.get('status')}"
        ),
        request_id=request.headers.get("X-Request-ID"),
        event_type="ML_DATA_INGESTION",
        status="SUCCESS",
    )

    return {
        "message": "Kaggle dataset ingested successfully.",
        "summary": summary,
    }


@router.post("/admin/training/retrain", dependencies=[Depends(rate_limit_admin)])
def trigger_model_retrain(
    payload: RetrainRequest,
    request: Request,
    current_user: UserContext = Depends(require_roles([ROLE_ADMIN])),
):
    """Trigger a full ML retraining run using the specified data source (Admin only).

    Trains Logistic Regression (baseline), Random Forest, and Gradient Boosting
    candidates using stratified splits and SMOTE on the training fold.
    The best model (by composite Recall + PR-AUC score) is optionally promoted
    to production in the model registry.

    The ``data_source`` tag is stored in the model registry metadata for full
    traceability of which dataset produced each model version.
    """
    if payload.data_source not in ("synthetic", "kaggle", "telco"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data_source '{payload.data_source}'. Must be 'synthetic', 'kaggle', or 'telco'.",
        )

    from ml_engine.pipelines.training import train_churn_classification_pipeline

    try:
        result = train_churn_classification_pipeline(
            promote_best=payload.promote_best,
            data_source=payload.data_source,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Training data not found: {exc}. "
                "Run kaggle-ingest or telco-ingest first."
            ),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model retraining failed: {exc}",
        )

    log_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="MODEL_RETRAIN",
        target_resource=f"model:{result.get('best_model_name')}:{result.get('promoted_version')}",
        details=(
            f"Retrained on data_source='{payload.data_source}'. "
            f"Best model: {result.get('best_model_name')} "
            f"promoted as {result.get('promoted_version')}."
        ),
        request_id=request.headers.get("X-Request-ID"),
        event_type="MODEL_RETRAIN",
        status="SUCCESS",
    )

    return {
        "message": "Model retraining completed successfully.",
        "result": result,
    }


@router.get("/admin/training/dataset-registry", dependencies=[Depends(rate_limit_admin)])
def get_dataset_registry(
    current_user: UserContext = Depends(require_roles([ROLE_ADMIN])),
):
    """List all registered datasets with provenance and SHA-256 checksums (Admin only).

    Returns the full content of ``data/raw/dataset_registry.json`` so admins
    can audit which datasets were used to train each model version.
    """
    from ml_engine.pipelines.dataset_registry import DatasetRegistry

    registry = DatasetRegistry()
    datasets = registry.list_datasets()
    return {
        "total": len(datasets),
        "datasets": datasets,
    }


@router.post("/admin/training/telco-ingest", dependencies=[Depends(rate_limit_admin)])
def trigger_telco_ingestion(
    payload: TelcoIngestRequest,
    request: Request,
    current_user: UserContext = Depends(require_roles([ROLE_ADMIN])),
):
    """Ingest the IBM Telco Customer Churn CSV through the canonical ML pipeline (Admin only).

    Downloads from Kaggle: ``blastchar/telco-customer-churn``.
    Default file path: ``data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv``.
    """
    from ml_engine.pipelines.ingestion import run_batch_ingestion

    csv_path = Path(payload.telco_csv_path)

    try:
        summary = run_batch_ingestion(
            source="telco",
            raw_telco_path=csv_path,
            db_path=None,
            schedule_type=payload.schedule_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Telco ingestion failed: {exc}",
        )

    log_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="TELCO_INGEST",
        target_resource=f"file:{payload.telco_csv_path}",
        details=(
            f"Ingested {summary.get('rows_ingested', 0):,} rows from "
            f"'{payload.telco_csv_path}'. Status: {summary.get('status')}"
        ),
        request_id=request.headers.get("X-Request-ID"),
        event_type="ML_DATA_INGESTION",
        status="SUCCESS",
    )

    return {
        "message": "Telco dataset ingested successfully.",
        "summary": summary,
    }
