"""Pydantic Schemas for Model Monitoring Endpoints."""

from typing import Any
from pydantic import BaseModel


class ConfusionMatrixData(BaseModel):
    tn: int
    fp: int
    fn: int
    tp: int


class MetricRun(BaseModel):
    version: str
    model_name: str
    registered_at: str
    status: str
    precision: float
    recall: float
    f1: float
    roc_auc: float
    pr_auc: float
    confusion_matrix: ConfusionMatrixData


class FeatureDriftItem(BaseModel):
    feature_name: str
    baseline_mean: float
    current_mean: float
    drift_score: float
    status: str  # STABLE / DRIFTING


class ModelMetricsResponse(BaseModel):
    current_model_version: str
    promoted_model_name: str
    history: list[MetricRun]
    drift_report: list[FeatureDriftItem]
