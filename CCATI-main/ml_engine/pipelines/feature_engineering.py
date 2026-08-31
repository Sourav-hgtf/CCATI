"""Feature Engineering Pipeline (TICKET-102).

Computes derived features: usage trend deltas, rolling averages, call frequency, tenure buckets.
"""

import numpy as np
import pandas as pd


def compute_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute feature engineering transformations on raw usage dataframe."""
    df_feat = df.copy()

    # 1. Call minutes drop-off percentage (m3 -> m1)
    # Avoid division by zero
    m3_calls = np.maximum(df_feat["call_minutes_m3"], 1.0)
    df_feat["usage_drop_call_pct"] = ((m3_calls - df_feat["call_minutes_m1"]) / m3_calls).clip(-1.0, 1.0).round(4)

    # 2. Data usage drop-off percentage (m3 -> m1)
    m3_data = np.maximum(df_feat["data_gb_m3"], 0.1)
    df_feat["usage_drop_data_pct"] = ((m3_data - df_feat["data_gb_m1"]) / m3_data).clip(-1.0, 1.0).round(4)

    # 3. Support call trend (m1 - m3)
    df_feat["support_call_trend"] = df_feat["support_calls_m1"] - df_feat["support_calls_m3"]

    if "recharge_count_m1" not in df_feat.columns:
        df_feat["recharge_count_m1"] = 0
    if "recharge_count_m2" not in df_feat.columns:
        df_feat["recharge_count_m2"] = 0
    if "recharge_count_m3" not in df_feat.columns:
        df_feat["recharge_count_m3"] = 0
    df_feat["avg_monthly_recharges"] = np.round((df_feat["recharge_count_m1"] + df_feat["recharge_count_m2"] + df_feat["recharge_count_m3"]) / 3.0, 2)

    # 5. Tenure Buckets
    def get_tenure_bucket(tenure):
        if tenure <= 12:
            return "0-12m"
        elif tenure <= 24:
            return "12-24m"
        elif tenure <= 48:
            return "24-48m"
        else:
            return "48m+"

    df_feat["tenure_bucket"] = df_feat["tenure_months"].apply(get_tenure_bucket)

    return df_feat


def get_feature_definitions() -> dict[str, str]:
    """Return dictionary of feature definitions for documentation/metadata."""
    return {
        "usage_drop_call_pct": "Percentage drop in call minutes from month 3 to month 1",
        "usage_drop_data_pct": "Percentage drop in data usage (GB) from month 3 to month 1",
        "support_call_trend": "Difference in customer service call count between month 1 and month 3",
        "avg_monthly_recharges": "Average number of recharges per month over the last 3 months",
        "tenure_bucket": "Categorical bucket for customer tenure in months (0-12m, 12-24m, 24-48m, 48m+)",
    }
