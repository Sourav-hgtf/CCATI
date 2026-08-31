"""Pydantic Schemas for Aggregated Backend Analytics."""

from pydantic import BaseModel


class OverviewMetricsResponse(BaseModel):
    total_customers: int
    active_customers: int
    active_customers_change: float = 0.0
    churn_rate: float
    churn_rate_change: float = 0.0
    revenue_at_risk: float
    revenue_at_risk_change: float = 0.0
    high_risk_customers: int
    high_risk_customers_change: float = 0.0
    medium_risk_customers: int = 0
    low_risk_customers: int = 0
    average_churn_probability: float = 0.0
    customers_saved: int = 0
    customers_saved_change: float = 0.0
    retention_roi: float = 0.0
    retention_roi_change: float = 0.0


class ChurnTrendPointResponse(BaseModel):
    time_period: str
    churn_rate: float
    customers_at_risk: int


class RiskDistributionPointResponse(BaseModel):
    tier: str
    count: int
    percentage: float
    revenue_at_risk: float


class ContractBreakdownResponse(BaseModel):
    contract: str
    churn_rate: float
    customers: int


class TenureBreakdownResponse(BaseModel):
    tier: str
    churn_rate: float
    customers: int
