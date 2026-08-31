"""Pydantic Schemas for Batch Scoring Job Triggers & Real-time Predictions (TASK 13)."""

from pydantic import BaseModel, Field


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
    display_name: str = ""
    feature_value: str | float | int = ""
    contribution: float
    impact: str = "Increase"  # "Increase" or "Decrease"
    direction: str = "INCREASES_CHURN"  # "INCREASES_CHURN" or "DECREASES_CHURN"
    effect: str = "Increases churn risk"  # "Increases churn risk" or "Reduces churn risk"
    category: str = "General"
    importance: float | None = None


class DetailedExplanation(BaseModel):
    explanation_status: str = "AVAILABLE"  # "AVAILABLE" or "UNAVAILABLE"
    base_value: float = 0.50
    top_positive_drivers: list[FeatureAttributionItem] = Field(default_factory=list)
    top_negative_drivers: list[FeatureAttributionItem] = Field(default_factory=list)
    all_drivers: list[FeatureAttributionItem] = Field(default_factory=list)
    summary: str = ""
    disclaimer: str = "Feature contribution explains the model's prediction; it does not prove causation."


class PredictResponse(BaseModel):
    prediction_id: str = ""
    customer_id: str
    churn_probability: float
    risk_tier: str
    confidence_score: float
    threshold: float = 0.50
    decision: str = "RETENTION_INTERVENTION_RECOMMENDED"
    decision_reason: str = ""
    model_name: str
    model_version: str
    prediction_timestamp: str
    top_features: list[FeatureAttributionItem] = Field(default_factory=list)
    recommended_action: str = ""
    explanation: DetailedExplanation = Field(default_factory=DetailedExplanation)


class PredictionHistoryItem(BaseModel):
    prediction_id: str
    customer_id: str
    churn_probability: float
    prediction: int
    risk_tier: str
    confidence_score: float
    threshold: float = 0.50
    decision: str = "RETENTION_INTERVENTION_RECOMMENDED"
    decision_reason: str = ""
    model_name: str
    model_version: str
    prediction_timestamp: str
    recommended_action: str | None = None
    top_features: list[FeatureAttributionItem] = Field(default_factory=list)
    explanation: DetailedExplanation = Field(default_factory=DetailedExplanation)


class PredictionHistoryPaginatedResponse(BaseModel):
    items: list[PredictionHistoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int

