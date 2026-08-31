"""Pydantic Schemas for Batch Scoring Job Triggers."""

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
    customer_id: str
    churn_probability: float
    risk_tier: str
    confidence_score: float
    model_name: str
    model_version: str
    prediction_timestamp: str
    top_features: list[FeatureAttributionItem] = []
    recommended_action: str = ""

