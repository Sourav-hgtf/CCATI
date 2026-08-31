"""Data Quality Monitoring and Input Validation API Endpoints (TASK 11)."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from backend.app.core.rbac import UserContext, require_roles
from backend.app.services.data_quality import DataQualityEngine

router = APIRouter()


class DataQualityIssueItem(BaseModel):
    field: str
    issue_type: str
    severity: str
    message: str
    value: Any = None


class CustomerValidationResponse(BaseModel):
    customer_id: str
    is_valid: bool
    has_critical_errors: bool
    can_proceed_to_inference: bool
    quality_score: float
    quality_status: str
    issues: list[DataQualityIssueItem] = []
    issue_count: int
    timestamp: str


class FieldIssueSummary(BaseModel):
    field: str
    issue_type: str
    severity: str
    affected_count: int
    sample_message: str


class DataQualityReportResponse(BaseModel):
    overall_quality_score: float
    quality_status: str
    total_records: int
    valid_records: int
    invalid_records: int
    duplicate_count: int
    missing_values_count: int
    field_issues: list[FieldIssueSummary] = []
    timestamp: str
    alerts: list[dict[str, Any]] = []


@router.get("/data-quality", response_model=DataQualityReportResponse)
@router.get("/monitoring/data-quality", response_model=DataQualityReportResponse)
def get_data_quality_report(
    current_user: UserContext = Depends(require_roles(["Admin", "Analyst", "RetentionManager", "Executive"])),
):
    """GET /api/v1/data-quality — Return database-wide Data Quality audit and metrics."""
    engine = DataQualityEngine()
    report = engine.audit_database_quality()
    return DataQualityReportResponse(**report)


@router.post("/data-quality/validate", response_model=CustomerValidationResponse)
def validate_customer_data(
    payload: dict[str, Any],
    current_user: UserContext = Depends(require_roles(["Admin", "Analyst", "RetentionManager", "Executive"])),
):
    """POST /api/v1/data-quality/validate — Validate customer input data without invoking model inference."""
    engine = DataQualityEngine()
    res = engine.validate_record(payload)
    return CustomerValidationResponse(**res)


@router.get("/data-quality/customer/{customer_id}", response_model=CustomerValidationResponse)
def get_customer_data_quality(
    customer_id: str,
    current_user: UserContext = Depends(require_roles(["Admin", "Analyst", "RetentionManager", "Executive"])),
):
    """GET /api/v1/data-quality/customer/{customer_id} — Check data quality score for a stored subscriber."""
    import sqlite3
    from backend.app.core.config import settings

    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE LOWER(customer_id) = LOWER(?)", (customer_id.strip(),))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer record '{customer_id}' not found.",
        )

    engine = DataQualityEngine()
    res = engine.validate_record(dict(row))
    return CustomerValidationResponse(**res)
