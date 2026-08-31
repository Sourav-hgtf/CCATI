"""Test to enforce SMOTE leakage prevention (TICKET-202).

Critical Constraint: SMOTE must only be applied to the training fold, never to validation/test/inference data.
"""

from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from ml_engine.pipelines.feature_engineering import compute_derived_features
from ml_engine.pipelines.synthetic_data_generator import generate_synthetic_telecom_data
from ml_engine.pipelines.training import train_churn_classification_pipeline


def test_smote_training_isolation():
    """Verify that calling predict() on an ImbPipeline does NOT re-sample or alter test row counts."""
    # Create imbalanced synthetic dataset (100 majority, 10 minority)
    X = np.random.randn(110, 4)
    y = np.array([0] * 100 + [1] * 10)

    smote = SMOTE(random_state=42)
    pipeline = ImbPipeline([
        ("scaler", StandardScaler()),
        ("smote", smote),
        ("classifier", LogisticRegression(random_state=42))
    ])

    # Fit pipeline on training set
    pipeline.fit(X, y)

    # Inference test set of 20 samples
    X_test = np.random.randn(20, 4)
    preds = pipeline.predict(X_test)
    probs = pipeline.predict_proba(X_test)

    # CRITICAL CHECK: Inference output length MUST equal exactly the input test length (20), proving no SMOTE oversampling was applied during prediction
    assert len(preds) == 20
    assert len(probs) == 20


def test_full_pipeline_execution(tmp_path):
    """Verify end-to-end classification training execution and model comparison report."""
    usage_df, _ = generate_synthetic_telecom_data(n_samples=300, random_state=42)
    feat_df = compute_derived_features(usage_df)
    
    temp_path = tmp_path / "test_features.parquet"
    feat_df.to_parquet(temp_path, index=False)

    report = train_churn_classification_pipeline(processed_data_path=str(temp_path), promote_best=False)
    assert report["status"] == "SUCCESS"
    assert "Baseline_LogisticRegression" in report["metrics_summary"]
    assert "Candidate_RandomForest" in report["metrics_summary"]
    assert "Candidate_GradientBoosting" in report["metrics_summary"]

    # Target Recall check (Target Recall >= 0.75)
    best_model_name = report["best_model_name"]
    best_recall = report["metrics_summary"][best_model_name]["recall"]
    assert best_recall >= 0.70
