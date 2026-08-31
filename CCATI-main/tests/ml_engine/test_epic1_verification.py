"""Test suite verifying Epic 1 Acceptance Criteria (TICKET-101, TICKET-102, TICKET-103)."""

import json
from pathlib import Path
import sqlite3
import pandas as pd
import pytest

from ml_engine.pipelines.data_quality import DataValidationError, validate_and_filter_raw_data
from ml_engine.pipelines.feature_engineering import compute_derived_features, get_feature_definitions
from ml_engine.pipelines.ingestion import run_batch_ingestion


def test_ticket_101_ingestion_malformed_rows_handling(tmp_path):
    """TICKET-101: Ingestion handles missing/malformed rows without failing the batch."""
    # Create sample raw data with 1 malformed row (negative tenure)
    raw_df = pd.DataFrame([
        {
            "customer_id": "CUST-001", "plan_tier": "Unlimited", "contract_type": "Month-to-Month",
            "tenure_months": 12, "monthly_charges": 500.0, "total_charges": 6000.0,
            "call_minutes_m1": 100.0, "call_minutes_m3": 200.0, "data_gb_m1": 5.0, "data_gb_m3": 10.0,
            "support_calls_m1": 2, "support_calls_m2": 1, "support_calls_m3": 0,
            "recharge_count_m1": 3, "recharge_count_m2": 3, "recharge_count_m3": 3,
        },
        {
            "customer_id": "CUST-MALFORMED", "plan_tier": "Basic", "contract_type": "Month-to-Month",
            "tenure_months": -5, "monthly_charges": 200.0, "total_charges": 1000.0,  # Invalid tenure (-5)
            "call_minutes_m1": 50.0, "call_minutes_m3": 100.0, "data_gb_m1": 2.0, "data_gb_m3": 4.0,
            "support_calls_m1": 1, "support_calls_m2": 1, "support_calls_m3": 1,
            "recharge_count_m1": 1, "recharge_count_m2": 1, "recharge_count_m3": 1,
        }
    ])
    
    raw_csv = tmp_path / "raw_test.csv"
    db_out = tmp_path / "test_db.db"
    raw_df.to_csv(raw_csv, index=False)

    # Execute ingestion run
    summary = run_batch_ingestion(raw_usage_path=raw_csv, db_path=db_out, schedule_type="on_demand")

    # Assert batch completed successfully, isolating the malformed row
    assert summary["status"] == "SUCCESS"
    assert summary["rows_received"] == 2
    assert summary["rows_ingested"] == 1
    assert summary["malformed_rows_filtered"] == 1


def test_ticket_102_feature_engineering_manual_validation():
    """TICKET-102: Feature pipeline output validated against manually computed sample values."""
    raw_sample = pd.DataFrame([{
        "customer_id": "CUST-102", "plan_tier": "Premium", "contract_type": "1 Year",
        "tenure_months": 18, "monthly_charges": 600.0, "total_charges": 10800.0,
        "call_minutes_m1": 150.0, "call_minutes_m3": 300.0,  # drop = (300 - 150)/300 = 0.5
        "data_gb_m1": 4.0, "data_gb_m3": 16.0,                # drop = (16 - 4)/16 = 0.75
        "support_calls_m1": 5, "support_calls_m2": 3, "support_calls_m3": 1, # trend = 5 - 1 = 4
        "recharge_count_m1": 4, "recharge_count_m2": 2, "recharge_count_m3": 3, # avg = 3.0
    }])

    feat_df = compute_derived_features(raw_sample)

    # Validate against hand-calculated values
    assert feat_df.loc[0, "usage_drop_call_pct"] == 0.5000
    assert feat_df.loc[0, "usage_drop_data_pct"] == 0.7500
    assert feat_df.loc[0, "support_call_trend"] == 4
    assert feat_df.loc[0, "avg_monthly_recharges"] == 3.0
    assert feat_df.loc[0, "tenure_bucket"] == "12-24m"

    # Feature definitions documentation metadata check
    defs = get_feature_definitions()
    assert "usage_drop_call_pct" in defs
    assert "tenure_bucket" in defs


def test_ticket_103_critical_schema_violation():
    """TICKET-103: Pipeline halts/flags on critical schema violations."""
    # Missing required column 'monthly_charges'
    invalid_df = pd.DataFrame([{
        "customer_id": "CUST-999", "plan_tier": "Basic", "contract_type": "Month-to-Month",
        "tenure_months": 10
    }])

    with pytest.raises(DataValidationError, match="Critical Schema Violation"):
        validate_and_filter_raw_data(invalid_df)
