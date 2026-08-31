"""Unsupervised K-Means Customer Segmentation Pipeline (EPIC 3 & TASK 14).

Provides:
1. Feature extraction and standard scaling for behavioral clustering.
2. Production K-Means clustering with deterministic random seed and quality evaluation.
3. Intelligent deterministic segment naming and health scoring.
4. Clustering quality metrics (Silhouette Score, Davies-Bouldin Index, Calinski-Harabasz Index).
5. PCA 2D scatter coordinates generation.
6. Segment artifact serialization, loading, and real-time single-customer assignment.
7. Business value / ROI opportunity estimation per segment.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler

from ml_engine.config import (
    CLUSTERING_FEATURES,
    DEFAULT_K_CLUSTERS,
    MODEL_REGISTRY_DIR,
)

SEGMENTATION_ARTIFACT_PATH = MODEL_REGISTRY_DIR / "segmentation_artifacts.joblib"
SEGMENTATION_METADATA_PATH = MODEL_REGISTRY_DIR / "segmentation_metadata.json"

# In-memory artifact cache
_SEGMENTATION_CACHE: dict[str, Any] = {}


def prepare_and_scale_features(
    df: pd.DataFrame,
    scaler: StandardScaler | None = None,
    min_risk_threshold: float | None = None,
) -> tuple[np.ndarray, StandardScaler, pd.DataFrame]:
    """Prepare and standardize numerical features for K-Means clustering.

    If scaler is provided, applies transform (inference mode).
    If scaler is None, fits a new StandardScaler on the features (training mode).
    """
    if min_risk_threshold is not None and "churn_probability" in df.columns:
        df_target = df[df["churn_probability"] >= min_risk_threshold].copy()
        if len(df_target) < 10:
            df_target = df.copy()  # Fallback if target slice is too small
    else:
        df_target = df.copy()

    # Ensure required clustering features exist
    available_cols = [c for c in CLUSTERING_FEATURES if c in df_target.columns]
    if len(available_cols) < len(CLUSTERING_FEATURES):
        from ml_engine.pipelines.feature_engineering import compute_derived_features
        df_target = compute_derived_features(df_target)

    X_cluster = df_target[CLUSTERING_FEATURES].copy()
    X_cluster = X_cluster.fillna(X_cluster.median())

    if scaler is None:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_cluster)
    else:
        X_scaled = scaler.transform(X_cluster)

    return X_scaled, scaler, df_target


def compute_clustering_quality_metrics(
    X_scaled: np.ndarray, cluster_labels: np.ndarray
) -> dict[str, Any]:
    """Calculate mathematical clustering evaluation metrics."""
    n_samples = len(X_scaled)
    n_clusters = len(np.unique(cluster_labels))

    if n_samples < 5 or n_clusters < 2:
        return {
            "silhouette_score": 0.0,
            "davies_bouldin_index": 0.0,
            "calinski_harabasz_index": 0.0,
            "n_clusters": n_clusters,
            "evaluated_subscribers": n_samples,
            "interpretation": "Insufficient sample size or cluster diversity for quality metrics.",
        }

    try:
        sil = float(silhouette_score(X_scaled, cluster_labels))
    except Exception:
        sil = 0.0

    try:
        db = float(davies_bouldin_score(X_scaled, cluster_labels))
    except Exception:
        db = 0.0

    try:
        ch = float(calinski_harabasz_score(X_scaled, cluster_labels))
    except Exception:
        ch = 0.0

    return {
        "silhouette_score": round(sil, 4),
        "davies_bouldin_index": round(db, 4),
        "calinski_harabasz_index": round(ch, 2),
        "n_clusters": int(n_clusters),
        "evaluated_subscribers": int(n_samples),
        "interpretation": (
            f"Silhouette Score ({sil:.3f}) measures cluster cohesion vs separation (higher is better, >0.25 is solid for customer behavior). "
            f"Davies-Bouldin Index ({db:.3f}) measures cluster similarity (lower is better). "
            f"Calinski-Harabasz Index ({ch:.1f}) measures variance ratio (higher indicates denser, well-separated clusters)."
        ),
    }


def run_kmeans_clustering(
    X_scaled: np.ndarray,
    k: int = DEFAULT_K_CLUSTERS,
    kmeans_model: KMeans | None = None,
) -> tuple[np.ndarray, float, KMeans]:
    """Execute K-Means clustering and return labels, silhouette score, and fitted model."""
    if kmeans_model is None:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X_scaled)
    else:
        kmeans = kmeans_model
        cluster_labels = kmeans.predict(X_scaled)

    metrics = compute_clustering_quality_metrics(X_scaled, cluster_labels)
    sil_score = metrics["silhouette_score"]
    return cluster_labels, sil_score, kmeans


def compute_deterministic_segment_name_and_strategy(
    avg_churn_prob: float,
    avg_monthly_charges: float,
    avg_tenure: float,
    avg_support_calls: float,
    avg_call_drop: float,
    cluster_id: int,
) -> tuple[str, str, str]:
    """Derive intelligent business name, risk category, and retention strategy from segment statistics."""
    # High Risk Cluster Rules (Avg Churn Prob >= 0.50)
    if avg_churn_prob >= 0.50:
        if avg_monthly_charges >= 1100.0:
            name = "High-Value At-Risk Tier"
            risk_cat = "High Value Risk"
            strategy = "VIP Loyalty Bill Discount & Senior Account Manager Outreach"
        elif avg_tenure <= 24.0 or avg_support_calls >= 5.0:
            name = "Early-Tenure Service Escalation"
            risk_cat = "Early Churn Risk"
            strategy = "Priority Tech Support Outreach & Onboarding Incentive"
        elif avg_tenure >= 45.0 or avg_call_drop >= 0.45:
            name = "Long-Tenure Usage Fatigue"
            risk_cat = "Tenure Fatigue Risk"
            strategy = "1-Year Contract Renewal Bonus & Re-engagement Campaign"
        else:
            name = f"Elevated Risk Segment {cluster_id + 1}"
            risk_cat = "High Risk"
            strategy = "Proactive Retention & Service Recovery"
    else:
        # Low / Moderate Risk Cluster Rules (Avg Churn Prob < 0.50)
        if avg_monthly_charges >= 1000.0:
            name = "High-Value Premium Loyals"
            risk_cat = "VIP Loyals"
            strategy = "VIP Loyalty Bill Discount & Premium Speed Boost"
        elif avg_monthly_charges <= 700.0:
            name = "Budget-Friendly Loyal Subscribers"
            risk_cat = "Low Risk"
            strategy = "Digital Self-Service & Standard Loyalty Rewards"
        else:
            name = "Stable Mainstream Subscribers"
            risk_cat = "Low Risk"
            strategy = "Standard Engagement & Digital Upsell"

    return name, risk_cat, strategy


def compute_segment_health_score(
    avg_churn_prob: float,
    high_risk_ratio: float,
    avg_support_calls: float,
) -> tuple[float, str]:
    """Calculate segment health score (0-100) and operational health status.

    Formula:
      Health Score = 100 - (Avg Churn Prob * 50 + High Risk % * 30 + min(1.0, Avg Support / 5) * 20)
    """
    support_penalty = min(1.0, avg_support_calls / 5.0) * 20.0
    churn_penalty = avg_churn_prob * 50.0
    high_risk_penalty = high_risk_ratio * 30.0

    raw_health = 100.0 - (churn_penalty + high_risk_penalty + support_penalty)
    health_score = round(float(np.clip(raw_health, 0.0, 100.0)), 1)

    if health_score >= 70.0:
        health_status = "HEALTHY"
    elif health_score >= 40.0:
        health_status = "MODERATE_RISK"
    else:
        health_status = "CRITICAL_RISK"

    return health_score, health_status


def compute_segment_risk_matrix(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Compute customer distribution across risk tiers per segment."""
    matrix = []
    for cid, group in df.groupby("cluster_id"):
        tier_counts = dict(group["risk_tier"].value_counts()) if "risk_tier" in group.columns else {}
        cluster_name = group["cluster_name"].iloc[0] if "cluster_name" in group.columns else f"Segment {int(cid) + 1}"
        total_subscribers = len(group)

        low_count = int(tier_counts.get("Low", 0))
        medium_count = int(tier_counts.get("Medium", 0))
        high_count = int(tier_counts.get("High", 0))
        critical_count = int(tier_counts.get("Critical", 0))

        matrix.append({
            "cluster_id": int(cid),
            "cluster_name": cluster_name,
            "low_risk_count": low_count,
            "medium_risk_count": medium_count,
            "high_risk_count": high_count,
            "critical_risk_count": critical_count,
            "total_count": total_subscribers,
            "high_critical_ratio": round((high_count + critical_count) / max(1, total_subscribers), 3),
        })
    return matrix


def compute_cluster_profiles(
    df: pd.DataFrame, cluster_labels: np.ndarray
) -> list[dict[str, Any]]:
    """Compute per-cluster aggregate metrics, health scores, ROI, and intelligent business profiles."""
    df_temp = df.copy()
    df_temp["cluster_id"] = cluster_labels

    profiles = []
    total_pop = len(df_temp)

    # Pre-calculate fallback names if needed
    for cid, group in df_temp.groupby("cluster_id"):
        size = len(group)
        pct = round((size / total_pop) * 100, 1)

        avg_tenure = round(float(group["tenure_months"].mean()), 1)
        avg_monthly = round(float(group["monthly_charges"].mean()), 2)
        avg_total = round(float(group["total_charges"].mean()), 2) if "total_charges" in group.columns else round(avg_tenure * avg_monthly, 2)
        avg_call_drop = round(float(group["usage_drop_call_pct"].mean()), 3) if "usage_drop_call_pct" in group.columns else 0.0
        avg_data_drop = round(float(group["usage_drop_data_pct"].mean()), 3) if "usage_drop_data_pct" in group.columns else 0.0
        avg_support = round(float(group["support_calls_m1"].mean()), 1) if "support_calls_m1" in group.columns else 0.0
        avg_churn_p = round(float(group["churn_probability"].mean()), 3) if "churn_probability" in group.columns else 0.0
        avg_clv = round(float(group["clv"].mean()), 2) if "clv" in group.columns else round(avg_monthly * 24.0, 2)
        avg_priority = round(float(group["priority_score"].mean()), 2) if "priority_score" in group.columns else round(avg_churn_p * 100.0, 2)

        # Count high and critical risk subscribers
        high_risk_subscribers = int(len(group[group["risk_tier"].isin(["High", "Critical"])])) if "risk_tier" in group.columns else int(len(group[group["churn_probability"] >= 0.50])) if "churn_probability" in group.columns else 0
        critical_risk_subscribers = int(len(group[group["risk_tier"] == "Critical"])) if "risk_tier" in group.columns else 0
        high_risk_ratio = high_risk_subscribers / max(1, size)

        # Actual churn rate if ground truth churn column exists
        if "churn" in group.columns:
            actual_churn = round(float(group["churn"].mean()) * 100.0, 1)
        else:
            actual_churn = round(avg_churn_p * 100.0, 1)

        # Name and strategy assignment
        name, risk_cat, strategy = compute_deterministic_segment_name_and_strategy(
            avg_churn_prob=avg_churn_p,
            avg_monthly_charges=avg_monthly,
            avg_tenure=avg_tenure,
            avg_support_calls=avg_support,
            avg_call_drop=avg_call_drop,
            cluster_id=int(cid),
        )

        # Health calculation
        health_score, health_status = compute_segment_health_score(
            avg_churn_prob=avg_churn_p,
            high_risk_ratio=high_risk_ratio,
            avg_support_calls=avg_support,
        )

        # ROI & business value calculation
        eligible_subs = high_risk_subscribers
        campaign_cost = round(eligible_subs * 75.0, 2)
        expected_saved_rev = round(eligible_subs * avg_clv * avg_churn_p * 0.35, 2)
        net_roi = round(expected_saved_rev - campaign_cost, 2)
        roi_pct = round((net_roi / max(1.0, campaign_cost)) * 100.0, 1) if campaign_cost > 0 else 0.0

        profile = {
            "cluster_id": int(cid),
            "cluster_name": name,
            "size": size,
            "percentage": pct,
            "avg_tenure_months": avg_tenure,
            "avg_monthly_charges": avg_monthly,
            "avg_total_charges": avg_total,
            "avg_usage_drop_call_pct": avg_call_drop,
            "avg_usage_drop_data_pct": avg_data_drop,
            "avg_support_calls_m1": avg_support,
            "avg_churn_probability": avg_churn_p,
            "actual_churn_rate": actual_churn,
            "avg_clv": avg_clv,
            "avg_priority_score": avg_priority,
            "high_risk_count": high_risk_subscribers,
            "critical_risk_count": critical_risk_subscribers,
            "health_score": health_score,
            "health_status": health_status,
            "risk_category": risk_cat,
            "recommended_strategy": strategy,
            "eligible_customers": eligible_subs,
            "estimated_campaign_cost": campaign_cost,
            "estimated_retention_opportunity": expected_saved_rev,
            "estimated_roi_pct": roi_pct,
        }
        profiles.append(profile)

    return profiles


def compute_2d_projections(
    X_scaled: np.ndarray, pca: PCA | None = None
) -> tuple[np.ndarray, PCA]:
    """Generate PCA 2D scatter coordinates for frontend visualization."""
    if pca is None:
        pca = PCA(n_components=2, random_state=42)
        coords_2d = pca.fit_transform(X_scaled)
    else:
        coords_2d = pca.transform(X_scaled)
    return coords_2d, pca


def save_segmentation_artifacts(
    kmeans: KMeans,
    scaler: StandardScaler,
    pca: PCA,
    quality_metrics: dict[str, Any],
    profiles: list[dict[str, Any]],
) -> None:
    """Serialize segmentation models and metadata to disk."""
    MODEL_REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "kmeans": kmeans,
        "scaler": scaler,
        "pca": pca,
        "features": CLUSTERING_FEATURES,
        "k": kmeans.n_clusters,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    joblib.dump(artifacts, SEGMENTATION_ARTIFACT_PATH)

    metadata = {
        "model_type": "KMeans",
        "n_clusters": kmeans.n_clusters,
        "features": CLUSTERING_FEATURES,
        "quality_metrics": quality_metrics,
        "profiles": profiles,
        "artifact_path": str(SEGMENTATION_ARTIFACT_PATH),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(SEGMENTATION_METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    # Invalidate cache
    _SEGMENTATION_CACHE.clear()


def load_segmentation_artifacts() -> dict[str, Any]:
    """Load fitted segmentation models and metadata from disk with caching."""
    if "artifacts" in _SEGMENTATION_CACHE:
        return _SEGMENTATION_CACHE["artifacts"]

    if not SEGMENTATION_ARTIFACT_PATH.exists():
        raise FileNotFoundError(
            f"Segmentation artifact file '{SEGMENTATION_ARTIFACT_PATH}' not found. Run batch scoring to generate."
        )

    artifacts = joblib.load(SEGMENTATION_ARTIFACT_PATH)
    if SEGMENTATION_METADATA_PATH.exists():
        with open(SEGMENTATION_METADATA_PATH, "r") as f:
            artifacts["metadata"] = json.load(f)
    else:
        artifacts["metadata"] = {}

    _SEGMENTATION_CACHE["artifacts"] = artifacts
    return artifacts


def assign_customer_segment(customer_data: dict[str, Any] | pd.DataFrame | pd.Series) -> dict[str, Any]:
    """Deterministically assign a customer to an existing segment using saved artifacts."""
    artifacts = load_segmentation_artifacts()
    kmeans: KMeans = artifacts["kmeans"]
    scaler: StandardScaler = artifacts["scaler"]
    pca: PCA = artifacts["pca"]
    profiles: list[dict[str, Any]] = artifacts.get("metadata", {}).get("profiles", [])

    if isinstance(customer_data, dict):
        df_cust = pd.DataFrame([customer_data])
    elif isinstance(customer_data, pd.Series):
        df_cust = pd.DataFrame([customer_data.to_dict()])
    else:
        df_cust = customer_data.copy()

    # Preprocess & scale features
    X_scaled, _, _ = prepare_and_scale_features(df_cust, scaler=scaler)
    cluster_id = int(kmeans.predict(X_scaled)[0])
    coords_2d, _ = compute_2d_projections(X_scaled, pca=pca)

    # Find matching profile
    matching_profile = next((p for p in profiles if p["cluster_id"] == cluster_id), None)
    if matching_profile:
        cluster_name = matching_profile["cluster_name"]
        risk_cat = matching_profile["risk_category"]
        strategy = matching_profile["recommended_strategy"]
        health_score = matching_profile["health_score"]
        health_status = matching_profile["health_status"]
    else:
        cluster_name = f"Segment {cluster_id + 1}"
        risk_cat = "General Risk"
        strategy = "Standard Customer Monitoring"
        health_score = 50.0
        health_status = "MODERATE_RISK"

    return {
        "cluster_id": cluster_id,
        "cluster_name": cluster_name,
        "pca_x": round(float(coords_2d[0, 0]), 4),
        "pca_y": round(float(coords_2d[0, 1]), 4),
        "risk_category": risk_cat,
        "recommended_strategy": strategy,
        "health_score": health_score,
        "health_status": health_status,
    }
