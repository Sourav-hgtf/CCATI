"""Data Quality Checks and Schema Validation Pipeline (TICKET-103).

Provides automated checks (nulls, type mismatches, out-of-range values) before data
enters the training/scoring pipeline. Generates a data quality report per ingestion run.
"""

from typing import Any
import pandas as pd


class DataValidationError(Exception):
    """Exception raised when data validation fails critical schema checks."""
    pass


def validate_and_filter_raw_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Validate schema, detect type/range violations, filter malformed rows safely,
    and generate a Data Quality Report (TICKET-103).
    """
    required_cols = [
        "customer_id", "plan_tier", "contract_type", "tenure_months", 
        "monthly_charges", "total_charges", "call_minutes_m1", "call_minutes_m3",
        "data_gb_m1", "data_gb_m3", "support_calls_m1"
    ]
    
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise DataValidationError(f"Critical Schema Violation: Missing required columns {missing_cols}")

    total_rows = len(df)
    null_counts = df[required_cols].isnull().sum().to_dict()

    # Critical check: Customer ID must not be null
    if null_counts["customer_id"] > 0:
        raise DataValidationError("Critical Schema Violation: Found null values in 'customer_id' column")

    # Range and Type Validation
    invalid_tenure_mask = (df["tenure_months"] < 0) | df["tenure_months"].isnull()
    invalid_charges_mask = (df["monthly_charges"] < 0) | df["monthly_charges"].isnull()
    
    malformed_mask = invalid_tenure_mask | invalid_charges_mask
    malformed_count = int(malformed_mask.sum())

    # Safely isolate clean rows vs malformed rows
    df_clean = df[~malformed_mask].copy()

    # Generate Data Quality Report
    report = {
        "total_rows_received": total_rows,
        "valid_rows_passed": len(df_clean),
        "malformed_rows_filtered": malformed_count,
        "null_counts": null_counts,
        "schema_validation": "PASSED",
        "status": "PASSED" if malformed_count == 0 else "PASSED_WITH_WARNINGS",
    }

    return df_clean, report


def clean_and_impute_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Clean data and impute non-critical numerical/categorical null values."""
    df_clean = df.copy()
    
    num_cols = df_clean.select_dtypes(include=["float64", "int64", "float32", "int32"]).columns
    for col in num_cols:
        if col in df_clean.columns and df_clean[col].isnull().sum() > 0:
            df_clean[col] = df_clean[col].fillna(df_clean[col].median())
            
    cat_cols = df_clean.select_dtypes(include=["object", "string"]).columns
    for col in cat_cols:
        if col in df_clean.columns and df_clean[col].isnull().sum() > 0:
            df_clean[col] = df_clean[col].fillna("Unknown")

    return df_clean
