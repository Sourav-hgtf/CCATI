"""Segment Endpoints (TICKET-504)."""

import sqlite3
from fastapi import APIRouter, Depends, HTTPException
from backend.app.core.config import settings
from backend.app.core.rbac import UserContext, get_current_user
from backend.app.schemas.segment import (
    ScatterPoint,
    SegmentDetailResponse,
    SegmentOverviewResponse,
    SegmentProfile,
)

router = APIRouter()


@router.get("/segments", response_model=SegmentOverviewResponse)
def get_segments_overview(
    current_user: UserContext = Depends(get_current_user),
):
    """TICKET-504: GET /api/v1/segments (cluster profiles + 2D scatter coordinates)."""
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Load segment profiles
    cursor.execute("SELECT * FROM segment_profiles ORDER BY cluster_id ASC")
    profile_rows = cursor.fetchall()
    profiles = [dict(p) for p in profile_rows]

    # Load 2D scatter plot coordinates
    cursor.execute("SELECT customer_id, pca_x, pca_y, cluster_id, churn_probability, risk_tier FROM customer_scores LIMIT 500")
    scatter_rows = cursor.fetchall()
    conn.close()

    points = [
        ScatterPoint(
            customer_id=r["customer_id"],
            x=r["pca_x"],
            y=r["pca_y"],
            cluster_id=r["cluster_id"],
            churn_probability=r["churn_probability"],
            risk_tier=r["risk_tier"],
        )
        for r in scatter_rows
    ]

    return SegmentOverviewResponse(
        segments=[SegmentProfile(**p) for p in profiles],
        scatter_points=points,
    )


@router.get("/segments/{segment_id}", response_model=SegmentDetailResponse)
def get_segment_detail(
    segment_id: int,
    current_user: UserContext = Depends(get_current_user),
):
    """GET /api/v1/segments/{id} (detailed segment profile and feature distributions)."""
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM segment_profiles WHERE cluster_id = ?", (segment_id,))
    profile_row = cursor.fetchone()
    if not profile_row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Segment {segment_id} not found")

    cursor.execute("SELECT COUNT(*) FROM customer_scores WHERE cluster_id = ?", (segment_id,))
    count = cursor.fetchone()[0]
    conn.close()

    profile = SegmentProfile(**dict(profile_row))

    # Mock feature distributions for comparative box plot / histograms
    feature_distributions = {
        "tenure_months": {"mean": profile.avg_tenure_months, "q25": max(1, profile.avg_tenure_months * 0.7), "q75": profile.avg_tenure_months * 1.3},
        "monthly_charges": {"mean": profile.avg_monthly_charges, "q25": profile.avg_monthly_charges * 0.8, "q75": profile.avg_monthly_charges * 1.2},
        "usage_drop_call_pct": {"mean": profile.avg_usage_drop_call_pct, "q25": profile.avg_usage_drop_call_pct * 0.5, "q75": min(1.0, profile.avg_usage_drop_call_pct * 1.4)},
    }

    return SegmentDetailResponse(
        profile=profile,
        feature_distributions=feature_distributions,
        total_customers=count,
    )
