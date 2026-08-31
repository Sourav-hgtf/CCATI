"""Pydantic Schemas for Customer List and Detail Endpoints."""

from typing import Any
from pydantic import BaseModel


class FeatureAttribution(BaseModel):
    feature: str
    importance: float
    direction: str


class ROIDetails(BaseModel):
    action_cost: float
    expected_saved_revenue: float
    net_saved_revenue: float
    roi_pct: float


class RecommendationPayload(BaseModel):
    action_code: str
    action_name: str
    description: str
    roi_details: ROIDetails
    actioned: bool = False
    actioned_at: str | None = None


class CustomerListItem(BaseModel):
    customer_id: str
    name: str
    phone: str
    plan_tier: str
    tenure_months: int
    monthly_charges: float
    churn_probability: float
    risk_tier: str
    priority_score: float
    usage_drop_call_pct: float
    support_calls_m1: int
    last_call_reason: str | None = "None"
    recommended_action: str
    segment_id: int = 0


class CustomerPaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[CustomerListItem]


class CustomerDetailResponse(BaseModel):
    customer_id: str
    name: str
    phone: str
    email: str
    is_pii_revealed: bool = False
    plan_tier: str
    contract_type: str
    payment_method: str
    tenure_months: int
    monthly_charges: float
    total_charges: float
    churn_probability: float
    risk_tier: str
    priority_score: float
    clv: float
    usage_history: list[dict[str, Any]]
    top_shap_features: list[FeatureAttribution]
    recommendation: RecommendationPayload
    call_log_history: list[dict[str, Any]]
    segment_id: int = 0
