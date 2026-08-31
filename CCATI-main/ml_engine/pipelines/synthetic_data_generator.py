"""Synthetic Telecom Dataset Generator.

Generates realistic sample telecom customer usage and customer service call log data.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from ml_engine.config import RAW_DATA_DIR


def generate_synthetic_telecom_data(n_samples: int = 1500, random_state: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate synthetic customer usage records and call logs.
    
    Returns:
        tuple of (usage_df, call_logs_df)
    """
    np.random.seed(random_state)

    customer_ids = [f"CUST-{10000 + i}" for i in range(n_samples)]
    names = [f"Customer {i+1}" for i in range(n_samples)]
    phones = [f"+91-98765-{10000 + i}" for i in range(n_samples)]
    emails = [f"user{i+1}@example.com" for i in range(n_samples)]
    regions = np.random.choice(["North", "South", "East", "West", "Central"], size=n_samples)
    plan_tiers = np.random.choice(["Prepaid Basic", "Prepaid Unlimited", "Postpaid Standard", "Postpaid Premium"], size=n_samples, p=[0.3, 0.4, 0.2, 0.1])
    contract_types = np.random.choice(["Month-to-Month", "One Year", "Two Year"], size=n_samples, p=[0.6, 0.25, 0.15])
    payment_methods = np.random.choice(["Auto-Debit", "UPI/Credit Card", "Electronic Check", "Mailed Check"], size=n_samples)

    tenure_months = np.random.randint(1, 72, size=n_samples)
    monthly_charges = np.random.uniform(299, 1499, size=n_samples).round(2)
    total_charges = (tenure_months * monthly_charges * np.random.uniform(0.9, 1.1, size=n_samples)).round(2)

    # Historical monthly usage data (m1 = most recent month, m3 = 3 months ago)
    # Higher churn probability for customers with decreasing usage
    call_minutes_m3 = np.random.uniform(100, 1000, size=n_samples).round(1)
    data_gb_m3 = np.random.uniform(5, 100, size=n_samples).round(1)
    recharge_count_m3 = np.random.randint(1, 6, size=n_samples)
    support_calls_m3 = np.random.randint(0, 3, size=n_samples)

    # Churn tendency simulation
    churn_prob_raw = (
        0.35 * (contract_types == "Month-to-Month") +
        0.25 * (tenure_months < 12) +
        0.20 * (monthly_charges > 799) -
        0.15 * (contract_types == "Two Year") +
        np.random.uniform(-0.1, 0.1, size=n_samples)
    )
    is_at_risk = churn_prob_raw > 0.4

    # At-risk customers experience usage drop-off and more support calls
    drop_factor = np.where(is_at_risk, np.random.uniform(0.3, 0.7, size=n_samples), np.random.uniform(0.9, 1.1, size=n_samples))
    support_increase = np.where(is_at_risk, np.random.randint(2, 6, size=n_samples), np.random.randint(0, 2, size=n_samples))

    call_minutes_m2 = (call_minutes_m3 * (drop_factor ** 0.5)).round(1)
    call_minutes_m1 = (call_minutes_m3 * drop_factor).round(1)

    data_gb_m2 = (data_gb_m3 * (drop_factor ** 0.5)).round(1)
    data_gb_m1 = (data_gb_m3 * drop_factor).round(1)

    recharge_count_m2 = np.maximum(1, (recharge_count_m3 * (drop_factor ** 0.5)).astype(int))
    recharge_count_m1 = np.maximum(1, (recharge_count_m3 * drop_factor).astype(int))

    support_calls_m2 = support_calls_m3 + np.random.randint(0, 2, size=n_samples)
    support_calls_m1 = support_calls_m2 + support_increase

    # Churn label (1 = Churned/At Risk, 0 = Retained) - imbalanced dataset (~22% churn)
    churn = np.where(is_at_risk & (np.random.rand(n_samples) > 0.15), 1, 0)

    usage_df = pd.DataFrame({
        "customer_id": customer_ids,
        "name": names,
        "phone": phones,
        "email": emails,
        "region": regions,
        "plan_tier": plan_tiers,
        "contract_type": contract_types,
        "payment_method": payment_methods,
        "tenure_months": tenure_months,
        "monthly_charges": monthly_charges,
        "total_charges": total_charges,
        "call_minutes_m1": call_minutes_m1,
        "call_minutes_m2": call_minutes_m2,
        "call_minutes_m3": call_minutes_m3,
        "data_gb_m1": data_gb_m1,
        "data_gb_m2": data_gb_m2,
        "data_gb_m3": data_gb_m3,
        "recharge_count_m1": recharge_count_m1,
        "recharge_count_m2": recharge_count_m2,
        "recharge_count_m3": recharge_count_m3,
        "support_calls_m1": support_calls_m1,
        "support_calls_m2": support_calls_m2,
        "support_calls_m3": support_calls_m3,
        "churn": churn,
    })

    # Generate customer service call logs
    call_log_reasons = [
        "Network Quality / Data Speed Slow",
        "Billing Discrepancy / High Charges",
        "Plan Upgrade Request",
        "Service Disconnection Query",
        "SIM / Network Activation Issue",
        "Competitor Offer Inquiry",
    ]
    call_log_sentiments = ["Negative", "Neutral", "Positive"]
    
    logs = []
    for cid in customer_ids:
        # Number of log entries matching customer's m1 support calls
        n_logs = usage_df.loc[usage_df["customer_id"] == cid, "support_calls_m1"].values[0]
        for _ in range(n_logs):
            reason = np.random.choice(call_log_reasons, p=[0.35, 0.25, 0.10, 0.15, 0.05, 0.10])
            sentiment = "Negative" if "Disconnection" in reason or "Slow" in reason or "Discrepancy" in reason else np.random.choice(call_log_sentiments)
            logs.append({
                "customer_id": cid,
                "call_reason": reason,
                "sentiment": sentiment,
                "resolved": np.random.choice([True, False], p=[0.6, 0.4]),
                "duration_sec": int(np.random.exponential(180) + 30),
            })
            
    call_logs_df = pd.DataFrame(logs)

    return usage_df, call_logs_df


def save_synthetic_data(output_dir: Path = RAW_DATA_DIR):
    """Generate and save sample CSV/Parquet files to data/raw/."""
    usage_df, call_logs_df = generate_synthetic_telecom_data()
    
    usage_path_csv = output_dir / "customer_usage_raw.csv"
    usage_path_parquet = output_dir / "customer_usage_raw.parquet"
    call_logs_path_csv = output_dir / "customer_call_logs_raw.csv"
    
    usage_df.to_csv(usage_path_csv, index=False)
    usage_df.to_parquet(usage_path_parquet, index=False)
    call_logs_df.to_csv(call_logs_path_csv, index=False)
    
    print(f"Saved synthetic datasets to {output_dir}")
    return usage_path_parquet, call_logs_path_csv


if __name__ == "__main__":
    save_synthetic_data()
