"""Unsupervised K-Means Customer Segmentation Pipeline (EPIC 3: TICKET-301, 302, 303, 304)."""

from typing import Any
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from ml_engine.config import CLUSTERING_FEATURES, DEFAULT_K_CLUSTERS


def prepare_and_scale_features(
    df: pd.DataFrame, min_risk_threshold: float = 0.5
) -> tuple[np.ndarray, StandardScaler, pd.DataFrame]:
    """TICKET-301: Prepare and standardize numerical features for K-Means clustering,
    filtering for subscribers meeting or exceeding the churn probability threshold (>= 0.5).
    """
    if "churn_probability" in df.columns:
        df_target = df[df["churn_probability"] >= min_risk_threshold].copy()
        if len(df_target) < 10:
            df_target = df.copy()  # Fallback if target sample size is too small
    else:
        df_target = df.copy()

    X_cluster = df_target[CLUSTERING_FEATURES].copy()
    X_cluster = X_cluster.fillna(X_cluster.median())

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_cluster)
    return X_scaled, scaler, df_target


def run_kmeans_clustering(
    X_scaled: np.ndarray, k: int = DEFAULT_K_CLUSTERS
) -> tuple[np.ndarray, float, KMeans]:
    """TICKET-302: Train K-Means model and compute silhouette score."""
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)
    sil_score = float(silhouette_score(X_scaled, cluster_labels))
    return cluster_labels, sil_score, kmeans


def compute_cluster_profiles(
    df: pd.DataFrame, cluster_labels: np.ndarray
) -> list[dict[str, Any]]:
    """TICKET-303: Compute per-cluster aggregate metrics and profiles."""
    df_temp = df.copy()
    df_temp["cluster_id"] = cluster_labels

    profiles = []
    total_pop = len(df_temp)

    for cid, group in df_temp.groupby("cluster_id"):
        size = len(group)
        pct = round((size / total_pop) * 100, 1)

        profile = {
            "cluster_id": int(cid),
            "cluster_name": f"Segment {int(cid) + 1}",
            "size": size,
            "percentage": pct,
            "avg_tenure_months": round(float(group["tenure_months"].mean()), 1),
            "avg_monthly_charges": round(float(group["monthly_charges"].mean()), 2),
            "avg_usage_drop_call_pct": round(float(group["usage_drop_call_pct"].mean()), 3),
            "avg_usage_drop_data_pct": round(float(group["usage_drop_data_pct"].mean()), 3),
            "avg_support_calls_m1": round(float(group["support_calls_m1"].mean()), 1),
            "avg_churn_probability": round(float(group["churn_probability"].mean()), 3) if "churn_probability" in group.columns else 0.0,
        }

        # Strategy label assignment based on profile
        if profile["avg_usage_drop_call_pct"] > 0.4 or profile["avg_support_calls_m1"] > 3:
            profile["recommended_strategy"] = "Proactive Retention & Service Recovery"
            profile["risk_category"] = "High Risk"
        elif profile["avg_monthly_charges"] > 899:
            profile["recommended_strategy"] = "VIP Loyalty Reward & Plan Review"
            profile["risk_category"] = "High Value Risk"
        elif profile["avg_tenure_months"] < 12:
            profile["recommended_strategy"] = "Onboarding Support & Contract Incentive"
            profile["risk_category"] = "Early Churn Risk"
        else:
            profile["recommended_strategy"] = "Standard Engagement & Usage Promotion"
            profile["risk_category"] = "Low Risk"

        profiles.append(profile)

    return profiles


def compute_2d_projections(X_scaled: np.ndarray) -> np.ndarray:
    """TICKET-304: Generate PCA 2D scatter coordinates for frontend visualization."""
    pca = PCA(n_components=2, random_state=42)
    coords_2d = pca.fit_transform(X_scaled)
    return coords_2d
