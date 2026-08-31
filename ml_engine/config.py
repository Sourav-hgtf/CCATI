"""ML Engine Configuration and Constants."""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODEL_REGISTRY_DIR = DATA_DIR / "models"
DATABASE_DIR = DATA_DIR / "database"

# Create directories if they don't exist
for d in [RAW_DATA_DIR, PROCESSED_DATA_DIR, MODEL_REGISTRY_DIR, DATABASE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Feature Configuration
CATEGORICAL_FEATURES = ["plan_tier", "contract_type", "payment_method", "region"]
NUMERICAL_FEATURES = [
    "tenure_months",
    "monthly_charges",
    "total_charges",
    "call_minutes_m1",
    "call_minutes_m2",
    "call_minutes_m3",
    "data_gb_m1",
    "data_gb_m2",
    "data_gb_m3",
    "recharge_count_m1",
    "recharge_count_m2",
    "recharge_count_m3",
    "support_calls_m1",
    "support_calls_m2",
    "support_calls_m3",
]

# Derived Features engineered by pipeline
DERIVED_FEATURES = [
    "usage_drop_call_pct",
    "usage_drop_data_pct",
    "support_call_trend",
    "avg_monthly_recharges",
    "tenure_bucket",
]

MODEL_FEATURE_SET = NUMERICAL_FEATURES + DERIVED_FEATURES + CATEGORICAL_FEATURES

# Target Variable
TARGET_COL = "churn"

# Default Model Training Config
RANDOM_STATE = 42
TEST_SIZE = 0.2
SMOTE_SAMPLING_STRATEGY = 0.8  # Oversample minority class to 80% of majority class in training fold

# Default Clustering Config
DEFAULT_K_CLUSTERS = 4
CLUSTERING_FEATURES = [
    "tenure_months",
    "monthly_charges",
    "usage_drop_call_pct",
    "usage_drop_data_pct",
    "support_calls_m1",
]
