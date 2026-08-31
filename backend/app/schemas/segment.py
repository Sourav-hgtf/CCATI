"""Pydantic Schemas for Segment Endpoints."""

from typing import Any
from pydantic import BaseModel


class ScatterPoint(BaseModel):
    customer_id: str
    x: float
    y: float
    cluster_id: int
    churn_probability: float
    risk_tier: str


class SegmentProfile(BaseModel):
    cluster_id: int
    cluster_name: str
    size: int
    percentage: float
    avg_tenure_months: float
    avg_monthly_charges: float
    avg_usage_drop_call_pct: float
    avg_usage_drop_data_pct: float
    avg_support_calls_m1: float
    avg_churn_probability: float
    recommended_strategy: str
    risk_category: str


class SegmentOverviewResponse(BaseModel):
    segments: list[SegmentProfile]
    scatter_points: list[ScatterPoint]


class SegmentDetailResponse(BaseModel):
    profile: SegmentProfile
    feature_distributions: dict[str, Any]
    total_customers: int
