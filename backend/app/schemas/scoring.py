"""Pydantic Schemas for Batch Scoring Job Triggers & Real-time Predictions."""

from pydantic import BaseModel


class ScoringJobTriggerRequest(BaseModel):
    job_type: str = "BATCH_SCORING"  # BATCH_SCORING or RETRAIN_AND_SCORE
    force_ingestion: bool = False


class ScoringJobResponse(BaseModel):
    job_id: str
    job_type: str
    status: str  # QUEUED, RUNNING, SUCCEEDED, FAILED
    started_at: str
    completed_at: str | None = None
    records_processed: int = 0
    message: str = ""


class PredictRequest(BaseModel):
    customer_id: str


class FeatureAttributionItem(BaseModel):
    feature_name: str
    feature_value: str | float | int
    contribution: float
    impact: str  # "Increase" or "Decrease"


class PredictResponse(BaseModel):
    prediction_id: str = ""
    customer_id: str
    churn_probability: float
    risk_tier: str
    confidence_score: float
    model_name: str
    model_version: str
    prediction_timestamp: str
    top_features: list[FeatureAttributionItem] = []
    recommended_action: str = ""


class PredictionHistoryItem(BaseModel):
    prediction_id: str
    customer_id: str
    churn_probability: float
    prediction: int
    risk_tier: str
    confidence_score: float
    threshold: float = 0.50
    model_name: str
    model_version: str
    prediction_timestamp: str
    recommended_action: str | None = None
    top_features: list[FeatureAttributionItem] = []


class PredictionHistoryPaginatedResponse(BaseModel):
    items: list[PredictionHistoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int
