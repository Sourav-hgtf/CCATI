"""Classification Training Pipeline (TICKET-201, TICKET-202, TICKET-203, TICKET-204).

Trains Logistic Regression baseline and candidate models (Random Forest, Gradient Boosting)
using stratified splits and SMOTE applied strictly on the training fold.

TASK-21: Added ``data_source`` parameter for dataset traceability in the model registry.
"""

from typing import Any
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml_engine.config import (
    CATEGORICAL_FEATURES,
    DERIVED_FEATURES,
    NUMERICAL_FEATURES,
    PROCESSED_DATA_DIR,
    RANDOM_STATE,
    SMOTE_SAMPLING_STRATEGY,
    TARGET_COL,
    TEST_SIZE,
)
from ml_engine.pipelines.evaluation import evaluate_classifier
from ml_engine.registry.model_registry import ModelRegistry


def build_preprocessor() -> ColumnTransformer:
    """Construct Scikit-learn ColumnTransformer for numerical scaling and categorical OHE."""
    num_cols = NUMERICAL_FEATURES + [f for f in DERIVED_FEATURES if f != "tenure_bucket"]
    cat_cols = CATEGORICAL_FEATURES + ["tenure_bucket"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
        ]
    )
    return preprocessor


def train_churn_classification_pipeline(
    processed_data_path: str | None = None,
    promote_best: bool = True,
    data_source: str = "synthetic",
) -> dict[str, Any]:
    """Execute complete supervised training workflow.

    Args:
        processed_data_path: Path to processed Parquet features file.
            Defaults to ``data/processed/customer_features.parquet``.
        promote_best: If True, promote the best-performing model to production.
        data_source: Tag indicating which dataset produced the features.
            ``"synthetic"`` (default) | ``"kaggle"``.  Stored in model registry
            metadata for full traceability (TASK-21).

    Returns:
        Report dict comparing baseline and candidate models, including
        ``data_source`` for auditability.
    """
    if processed_data_path is None:
        processed_data_path = PROCESSED_DATA_DIR / "customer_features.parquet"

    df = pd.read_parquet(processed_data_path)
    
    # Feature columns used in model
    feature_cols = [c for c in df.columns if c not in ["customer_id", "name", "phone", "email", TARGET_COL]]
    X = df[feature_cols]
    y = df[TARGET_COL].values

    # TICKET-201: Stratified train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    print(f"Training split shape: {X_train.shape}, Test split shape: {X_test.shape}")
    print(f"Train churn ratio: {y_train.mean():.4f}, Test churn ratio: {y_test.mean():.4f}")
    print(f"Data source: {data_source}")

    models_to_evaluate = {
        "Baseline_LogisticRegression": LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
        "Candidate_RandomForest": RandomForestClassifier(n_estimators=100, max_depth=8, random_state=RANDOM_STATE),
        "Candidate_GradientBoosting": GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, random_state=RANDOM_STATE),
    }

    registry = ModelRegistry()
    eval_results = {}
    best_model_name = None
    best_score = -1.0
    best_pipeline = None

    for model_name, clf in models_to_evaluate.items():
        preprocessor = build_preprocessor()
        smote = SMOTE(sampling_strategy=SMOTE_SAMPLING_STRATEGY, random_state=RANDOM_STATE)

        # Imbalance-learn pipeline ensures SMOTE is fit ONLY on training folds
        pipeline = ImbPipeline([
            ("preprocessor", preprocessor),
            ("smote", smote),
            ("classifier", clf)
        ])

        print(f"Fitting model: {model_name}...")
        pipeline.fit(X_train, y_train)

        # Inference on Test set (SMOTE is NOT applied here)
        y_pred = pipeline.predict(X_test)
        y_proba = pipeline.predict_proba(X_test)[:, 1]

        metrics = evaluate_classifier(y_test, y_pred, y_proba)
        eval_results[model_name] = metrics

        # Select best model based on Recall & PR-AUC (prioritized for imbalance)
        composite_score = 0.6 * metrics["recall"] + 0.4 * metrics["pr_auc"]
        if composite_score > best_score:
            best_score = composite_score
            best_model_name = model_name
            best_pipeline = pipeline

    print(f"Best model selected: {best_model_name} with composite score: {best_score:.4f}")

    # Register models — include data_source for full traceability (TASK-21)
    version_str = f"v{int(pd.Timestamp.now().timestamp())}"
    if promote_best and best_pipeline:
        registry.register_model(
            model=best_pipeline,
            model_name=best_model_name,
            version=version_str,
            metrics=eval_results[best_model_name],
            feature_names=feature_cols,
            hyperparameters={
                "random_state": RANDOM_STATE, 
                "test_size": TEST_SIZE,
                "data_source": data_source,
            },
            promote=True,
        )

    return {
        "status": "SUCCESS",
        "best_model_name": best_model_name,
        "promoted_version": version_str,
        "data_source": data_source,
        "metrics_summary": eval_results,
    }


if __name__ == "__main__":
    train_churn_classification_pipeline()
