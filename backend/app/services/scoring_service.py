"""Scoring Service Orchestrator (TICKET-506).

Orchestrates data loading, ML model inference, SHAP explanations, K-Means clustering,
business risk scoring, and database persistence.
"""

from datetime import datetime, timezone
import json
import sqlite3
from typing import Any
import pandas as pd
from backend.app.core.config import settings
from backend.app.core.logger import get_logger
from business_engine.recommendations import get_recommended_action
from business_engine.risk_scoring import calculate_risk_scores
from ml_engine.config import PROCESSED_DATA_DIR
from ml_engine.pipelines.clustering import (
    compute_2d_projections,
    compute_cluster_profiles,
    compute_clustering_quality_metrics,
    prepare_and_scale_features,
    run_kmeans_clustering,
    save_segmentation_artifacts,
)
from ml_engine.pipelines.explainability import compute_shap_explanations
from ml_engine.pipelines.ingestion import run_batch_ingestion
from ml_engine.pipelines.training import train_churn_classification_pipeline
from ml_engine.registry.model_registry import ModelRegistry

logger = get_logger("telecom_churn.scoring_service")


def run_full_scoring_job(force_ingestion: bool = True) -> dict[str, Any]:
    """Execute complete end-to-end scoring pipeline."""
    start_time = datetime.now(timezone.utc)
    
    # Step 1: Data Ingestion & Feature Engineering
    parquet_path = PROCESSED_DATA_DIR / "customer_features.parquet"
    if force_ingestion or not parquet_path.exists():
        logger.info("Starting batch ingestion", extra={"step": "ingestion"})
        run_batch_ingestion()

    df = pd.read_parquet(parquet_path)
    logger.info("Loaded customer feature records for scoring", extra={"record_count": len(df), "step": "data_load"})

    # Step 2: Load or Train Promoted Model
    registry = ModelRegistry()
    try:
        model, model_info = registry.get_model()
        logger.info("Loaded promoted model", extra={"model_version": model_info['version'], "step": "model_load"})
    except ValueError:
        logger.info("No promoted model found, training initial pipeline", extra={"step": "model_train"})
        train_churn_classification_pipeline()
        model, model_info = registry.get_model()

    # Step 3: Classification Model Inference
    feature_cols = model_info.get("feature_names", [c for c in df.columns if c not in ["customer_id", "name", "phone", "email", "churn"]])
    X_score = df[feature_cols]

    churn_probs = model.predict_proba(X_score)[:, 1]
    df["churn_probability"] = churn_probs

    # Step 4: SHAP Explainability
    logger.info("Computing SHAP feature attributions", extra={"step": "shap"})
    shap_results = compute_shap_explanations(model, X_score, top_n=5)

    # Step 5: Business Risk Scoring (Computed before profiling so profiles include CLV & Priority Scores)
    logger.info("Computing business risk scores", extra={"step": "risk_scoring"})
    risk_scores = calculate_risk_scores(
        churn_probabilities=churn_probs,
        monthly_charges=df["monthly_charges"].values,
        tenures=df["tenure_months"].values,
    )
    df["risk_tier"] = [r["risk_tier"] for r in risk_scores]
    df["priority_score"] = [r["priority_score"] for r in risk_scores]
    df["clv"] = [r["clv"] for r in risk_scores]

    # Step 6: K-Means Segmentation & PCA 2D Scatter Coordinates
    logger.info("Running K-Means customer segmentation", extra={"step": "clustering", "subscriber_count": len(df)})
    X_scaled, scaler, _ = prepare_and_scale_features(df)
    cluster_labels, sil_score, kmeans = run_kmeans_clustering(X_scaled, k=4)
    coords_2d, pca = compute_2d_projections(X_scaled)
    quality_metrics = compute_clustering_quality_metrics(X_scaled, cluster_labels)
    cluster_profiles = compute_cluster_profiles(df, cluster_labels)

    # Save segmentation artifacts to disk for fast deterministic single-customer assignments
    save_segmentation_artifacts(
        kmeans=kmeans,
        scaler=scaler,
        pca=pca,
        quality_metrics=quality_metrics,
        profiles=cluster_profiles,
    )

    df["cluster_id"] = cluster_labels
    df["pca_x"] = coords_2d[:, 0].round(4)
    df["pca_y"] = coords_2d[:, 1].round(4)

    # Step 7: Retention Recommendations & Record Hydration
    logger.info("Computing retention recommendations", extra={"step": "recommendations"})
    scored_records = []
    for i, row in df.iterrows():
        r_score = risk_scores[i]
        rec = get_recommended_action(
            risk_tier=r_score["risk_tier"],
            churn_prob=r_score["churn_probability"],
            clv=r_score["clv"],
            support_calls_m1=int(row["support_calls_m1"]),
            usage_drop_call_pct=float(row["usage_drop_call_pct"]),
            monthly_charges=float(row["monthly_charges"]),
        )

        record = {
            "customer_id": row["customer_id"],
            "name": row["name"],
            "phone": row["phone"],
            "email": row["email"],
            "region": row["region"],
            "plan_tier": row["plan_tier"],
            "contract_type": row["contract_type"],
            "payment_method": row["payment_method"],
            "tenure_months": int(row["tenure_months"]),
            "monthly_charges": float(row["monthly_charges"]),
            "total_charges": float(row["total_charges"]),
            "churn_probability": r_score["churn_probability"],
            "risk_tier": r_score["risk_tier"],
            "priority_score": r_score["priority_score"],
            "clv": r_score["clv"],
            "usage_drop_call_pct": float(row["usage_drop_call_pct"]),
            "usage_drop_data_pct": float(row["usage_drop_data_pct"]),
            "support_calls_m1": int(row["support_calls_m1"]),
            "cluster_id": int(row["cluster_id"]),
            "pca_x": float(row["pca_x"]),
            "pca_y": float(row["pca_y"]),
            "shap_json": json.dumps(shap_results[i]),
            "recommendation_json": json.dumps(rec),
            "actioned": False,
            "actioned_at": None,
        }
        scored_records.append(record)

    # Step 8: Persist Scored Records & Profiles to Database via SQLAlchemy
    from backend.app.db.session import SessionLocal
    from backend.app.db.models.customer import CustomerScore
    from backend.app.db.models.segment import SegmentProfile

    session = SessionLocal()
    try:
        session.query(CustomerScore).delete()
        for r in scored_records:
            session.add(CustomerScore(**r))
        session.query(SegmentProfile).delete()
        for p in cluster_profiles:
            session.add(SegmentProfile(**p))
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to persist scored records to PostgreSQL: {e}")
        raise
    finally:
        session.close()

    end_time = datetime.now(timezone.utc)
    execution_sec = (end_time - start_time).total_seconds()

    return {
        "status": "SUCCEEDED",
        "records_processed": len(scored_records),
        "model_version": model_info["version"],
        "clustering_metrics": quality_metrics,
        "execution_seconds": round(execution_sec, 2),
    }

