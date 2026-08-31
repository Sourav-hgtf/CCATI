"""Pydantic Schemas for Segment & Behavioral Intelligence Endpoints (TASK 14)."""

from typing import Any
from pydantic import BaseModel, Field


class ScatterPoint(BaseModel):
    customer_id: str
    x: float
    y: float
    cluster_id: int
    churn_probability: float
    risk_tier: str


class SegmentQualityMetrics(BaseModel):
    silhouette_score: float = Field(..., description="Silhouette coefficient measuring cluster cohesion and separation (-1 to 1)")
    davies_bouldin_index: float = Field(..., description="Davies-Bouldin index measuring cluster similarity (lower is better)")
    calinski_harabasz_index: float = Field(..., description="Calinski-Harabasz score measuring variance ratio (higher is better)")
    n_clusters: int
    evaluated_subscribers: int
    interpretation: str


class SegmentRiskMatrixRow(BaseModel):
    cluster_id: int
    cluster_name: str
    low_risk_count: int
    medium_risk_count: int
    high_risk_count: int
    critical_risk_count: int
    total_count: int
    high_critical_ratio: float


class SegmentROI(BaseModel):
    eligible_customers: int
    avg_clv: float
    estimated_campaign_cost: float
    estimated_retention_opportunity: float
    estimated_roi_pct: float


class SegmentMacroInsights(BaseModel):
    highest_risk_segment: str
    highest_risk_churn_prob: float
    largest_segment: str
    largest_segment_size: int
    highest_churn_volume_segment: str
    highest_churn_volume_count: int
    lowest_risk_segment: str
    lowest_risk_churn_prob: float


class SegmentProfile(BaseModel):
    cluster_id: int
    cluster_name: str
    size: int
    percentage: float
    avg_tenure_months: float
    avg_monthly_charges: float
    avg_total_charges: float = 0.0
    avg_usage_drop_call_pct: float
    avg_usage_drop_data_pct: float
    avg_support_calls_m1: float
    avg_churn_probability: float
    actual_churn_rate: float = 0.0
    avg_clv: float = 0.0
    avg_priority_score: float = 0.0
    high_risk_count: int = 0
    critical_risk_count: int = 0
    health_score: float = 50.0
    health_status: str = "MODERATE_RISK"
    recommended_strategy: str
    risk_category: str
    eligible_customers: int = 0
    estimated_campaign_cost: float = 0.0
    estimated_retention_opportunity: float = 0.0
    estimated_roi_pct: float = 0.0


class SegmentOverviewResponse(BaseModel):
    segments: list[SegmentProfile]
    scatter_points: list[ScatterPoint]
    quality_metrics: SegmentQualityMetrics | None = None
    risk_matrix: list[SegmentRiskMatrixRow] = Field(default_factory=list)
    macro_insights: SegmentMacroInsights | None = None


class SegmentDetailResponse(BaseModel):
    profile: SegmentProfile
    feature_distributions: dict[str, Any]
    total_customers: int
    roi_projection: SegmentROI | None = None
    risk_breakdown: dict[str, int] = Field(default_factory=dict)


class SegmentCustomerItem(BaseModel):
    customer_id: str
    name: str
    plan_tier: str
    contract_type: str
    tenure_months: int
    monthly_charges: float
    churn_probability: float
    risk_tier: str
    priority_score: float
    clv: float
    support_calls_m1: int
    usage_drop_call_pct: float
    cluster_id: int


class SegmentCustomerListResponse(BaseModel):
    cluster_id: int
    cluster_name: str
    total_customers: int
    page: int
    page_size: int
    total_pages: int
    customers: list[SegmentCustomerItem]


class SegmentSummaryResponse(BaseModel):
    total_segments: int
    total_subscribers: int
    macro_insights: SegmentMacroInsights
    quality_metrics: SegmentQualityMetrics
    segments_summary: list[SegmentProfile]
