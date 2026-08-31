"""Batch Data Ingestion Pipeline (TICKET-101, TICKET-102, TICKET-103).

Loads raw usage and call logs from source files (CSV/Parquet), runs schema validation and data quality checks,
safely filters malformed rows, computes feature engineering transformations, and saves outputs to Parquet & SQLite/Postgres.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any
import pandas as pd

from ml_engine.config import DATABASE_DIR, PROCESSED_DATA_DIR
from ml_engine.pipelines.data_quality import clean_and_impute_missing, validate_and_filter_raw_data
from ml_engine.pipelines.feature_engineering import compute_derived_features
from ml_engine.pipelines.synthetic_data_generator import save_synthetic_data


def run_batch_ingestion(
    raw_usage_path: Path | None = None,
    raw_call_logs_path: Path | None = None,
    db_path: Path = DATABASE_DIR / "telecom_churn.db",
    schedule_type: str = "on_demand",
) -> dict[str, Any]:
    """Execute batch ingestion pipeline (TICKET-101).
    
    Returns run summary dictionary with row counts, output paths, and quality status.
    """
    if raw_usage_path is None or not raw_usage_path.exists():
        print("Raw dataset not found. Generating synthetic telecom dataset...")
        raw_usage_path, raw_call_logs_path = save_synthetic_data()

    print(f"Ingesting raw usage data from: {raw_usage_path}")
    if str(raw_usage_path).endswith(".parquet"):
        df_usage = pd.read_parquet(raw_usage_path)
    else:
        df_usage = pd.read_csv(raw_usage_path)

    # 1. Data Quality Checks & Malformed Row Filtering (TICKET-103)
    df_valid, quality_report = validate_and_filter_raw_data(df_usage)
    print(f"Data Quality Check: {quality_report['status']} | Valid rows: {quality_report['valid_rows_passed']} | Malformed filtered: {quality_report['malformed_rows_filtered']}")

    # 2. Cleaning & Missing Value Imputation
    df_clean = clean_and_impute_missing(df_valid)

    # 3. Feature Engineering (TICKET-102)
    df_features = compute_derived_features(df_clean)

    # 4. Save Processed Feature Set to Parquet Store (Technical Architecture 3.1)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    processed_parquet_path = PROCESSED_DATA_DIR / "customer_features.parquet"
    df_features.to_parquet(processed_parquet_path, index=False)

    # Save Data Quality Report
    dq_report_path = PROCESSED_DATA_DIR / "dq_report.json"
    with open(dq_report_path, "w") as f:
        json.dump(quality_report, f, indent=2)

    # 5. Ingest into SQLite/PostgreSQL Database
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    df_features.to_sql("customers", conn, if_exists="replace", index=False)
    
    if raw_call_logs_path and raw_call_logs_path.exists():
        df_logs = pd.read_csv(raw_call_logs_path)
        df_logs.to_sql("call_logs", conn, if_exists="replace", index=False)
    
    conn.close()

    summary = {
        "status": "SUCCESS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "schedule_type": schedule_type,
        "rows_received": quality_report["total_rows_received"],
        "rows_ingested": len(df_features),
        "malformed_rows_filtered": quality_report["malformed_rows_filtered"],
        "parquet_output": str(processed_parquet_path),
        "database_output": str(db_path),
        "dq_report_path": str(dq_report_path),
        "quality_status": quality_report["status"],
    }
    print(f"Batch ingestion completed successfully: {summary}")
    return summary


if __name__ == "__main__":
    run_batch_ingestion()
