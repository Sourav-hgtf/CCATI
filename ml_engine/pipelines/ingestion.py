"""Batch Data Ingestion Pipeline (TICKET-101, TICKET-102, TICKET-103, TASK-21).

Loads raw usage and call logs from source files (CSV/Parquet), runs schema validation
and data quality checks, safely filters malformed rows, computes feature engineering
transformations, and saves outputs to Parquet & SQLite/Postgres.

TASK-21: Added ``source`` parameter to support multiple dataset sources:
  - ``"synthetic"``  : Auto-generated synthetic telecom data (default, unchanged)
  - ``"kaggle"``     : Cell2Cell Duke/Teradata Kaggle dataset
  - ``"telco"``      : IBM Watson / blastchar Telco Customer Churn dataset
                       (kaggle: blastchar/telco-customer-churn)

All non-synthetic paths are adapted to the canonical schema before passing
through the same DQ / feature-engineering / persistence steps.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any
import pandas as pd

from ml_engine.config import DATABASE_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR
from ml_engine.pipelines.data_quality import clean_and_impute_missing, validate_and_filter_raw_data
from ml_engine.pipelines.dataset_registry import DatasetRegistry
from ml_engine.pipelines.feature_engineering import compute_derived_features
from ml_engine.pipelines.kaggle_adapter import adapt_cell2cell_to_canonical, validate_cell2cell_schema
from ml_engine.pipelines.telco_adapter import adapt_telco_to_canonical, validate_telco_schema
from ml_engine.pipelines.synthetic_data_generator import save_synthetic_data


def run_batch_ingestion(
    raw_usage_path: Path | None = None,
    raw_call_logs_path: Path | None = None,
    db_path: Path = DATABASE_DIR / "telecom_churn.db",
    schedule_type: str = "on_demand",
    # ── TASK-21 ──────────────────────────────────────────────────────────────
    source: str = "synthetic",
    raw_kaggle_path: Path | None = None,
    raw_telco_path: Path | None = None,
) -> dict[str, Any]:
    """Execute batch ingestion pipeline (TICKET-101, TASK-21).

    Args:
        raw_usage_path: Path to the raw synthetic usage CSV/Parquet.  If None
            and ``source="synthetic"``, synthetic data is auto-generated.
        raw_call_logs_path: Path to the raw synthetic call-logs CSV.
        db_path: Target database path (SQLite for tests; None = PostgreSQL prod).
        schedule_type: Label for audit/logging (``"on_demand"`` | ``"scheduled"``).
        source: Data source tag:
            ``"synthetic"`` (default) | ``"kaggle"`` | ``"telco"``.
        raw_kaggle_path: Path to the Cell2Cell Kaggle CSV.  Required when
            ``source="kaggle"``.  The file is **never overwritten**.
        raw_telco_path: Path to the IBM Telco CSV.  Required when
            ``source="telco"``.  Defaults to
            ``data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv``.

    Returns:
        Run-summary dictionary with row counts, output paths, and quality status.
    """

    # ── TASK-21: Kaggle ingestion path ─────────────────────────────────────
    if source == "kaggle":
        return _run_kaggle_ingestion(
            raw_kaggle_path=raw_kaggle_path,
            db_path=db_path,
            schedule_type=schedule_type,
        )

    # ── TASK-21: IBM Telco ingestion path ───────────────────────────────────
    if source == "telco":
        return _run_telco_ingestion(
            raw_telco_path=raw_telco_path,
            db_path=db_path,
            schedule_type=schedule_type,
        )

    # ── Original synthetic ingestion path (completely unchanged) ───────────
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
    print(
        f"Data Quality Check: {quality_report['status']} | "
        f"Valid rows: {quality_report['valid_rows_passed']} | "
        f"Malformed filtered: {quality_report['malformed_rows_filtered']}"
    )

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

    # 5. Register synthetic dataset in registry
    try:
        registry = DatasetRegistry()
        registry.register_dataset(
            name="synthetic_latest",
            path=raw_usage_path,
            source="synthetic",
            row_count=len(df_features),
            notes="Auto-generated synthetic telecom dataset",
        )
    except Exception as exc:
        print(f"[DatasetRegistry] Warning: Could not register synthetic dataset: {exc}")

    # 6. Ingest into Database (SQLite for isolated unit tests, PostgreSQL for production)
    if db_path is not None and str(db_path).endswith(".db"):
        conn = sqlite3.connect(db_path)
        df_features.to_sql("customers", conn, if_exists="replace", index=False)
        if raw_call_logs_path and raw_call_logs_path.exists():
            df_logs = pd.read_csv(raw_call_logs_path)
            df_logs.to_sql("call_logs", conn, if_exists="replace", index=False)
        conn.close()
    else:
        from backend.app.db.session import SessionLocal
        from backend.app.db.models.customer import Customer, CallLog

        session = SessionLocal()
        try:
            session.query(Customer).delete()
            cust_records = df_features.to_dict(orient="records")
            for r in cust_records:
                session.add(Customer(**r))

            if raw_call_logs_path and raw_call_logs_path.exists():
                df_logs = pd.read_csv(raw_call_logs_path)
                session.query(CallLog).delete()
                log_records = df_logs.to_dict(orient="records")
                for lr in log_records:
                    session.add(CallLog(**lr))
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error persisting ingested data to PostgreSQL: {e}")
        finally:
            session.close()

    summary = {
        "status": "SUCCESS",
        "source": "synthetic",
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


def _run_kaggle_ingestion(
    raw_kaggle_path: Path | None,
    db_path: Path,
    schedule_type: str,
) -> dict[str, Any]:
    """TASK-21: Ingest the Cell2Cell Kaggle CSV through the canonical pipeline.

    The raw Kaggle CSV is **never modified**.  Processing steps:
    1. Schema validation (confirm Cell2Cell-family dataset)
    2. Adapter: Cell2Cell → canonical schema
    3. Standard DQ checks & malformed-row filtering
    4. Missing-value imputation
    5. Derived feature engineering
    6. Save to ``data/processed/kaggle_features.parquet`` (dataset-specific)
    7. Also save to ``data/processed/customer_features.parquet`` (training default)
    8. Register dataset with SHA-256 in ``data/raw/dataset_registry.json``
    9. Persist customers to database (SQLite for tests, PostgreSQL for prod)

    Args:
        raw_kaggle_path: Path to the Cell2Cell Kaggle CSV (required).
        db_path: Database target path.
        schedule_type: Audit label.

    Returns:
        Ingestion summary dictionary.

    Raises:
        ValueError: If ``raw_kaggle_path`` is None or does not exist.
        DataValidationError: If the CSV does not pass Cell2Cell schema checks.
    """
    if raw_kaggle_path is None:
        raise ValueError(
            "raw_kaggle_path is required when source='kaggle'. "
            "Download Cell2Cell CSV to data/raw/ and provide its path."
        )

    raw_kaggle_path = Path(raw_kaggle_path)
    if not raw_kaggle_path.exists():
        raise ValueError(
            f"Kaggle CSV not found at '{raw_kaggle_path}'. "
            "Place the Cell2Cell dataset CSV in data/raw/ and provide its path."
        )

    print(f"[Kaggle Ingestion] Loading Cell2Cell dataset from: {raw_kaggle_path}")
    df_raw = pd.read_csv(raw_kaggle_path, low_memory=False)
    total_raw_rows = len(df_raw)
    print(f"[Kaggle Ingestion] Loaded {total_raw_rows:,} rows, {len(df_raw.columns)} columns")

    # 1. Cell2Cell schema validation
    is_valid, missing_cols = validate_cell2cell_schema(df_raw)
    if not is_valid:
        from ml_engine.pipelines.data_quality import DataValidationError
        raise DataValidationError(
            f"Cell2Cell schema validation failed. "
            f"Missing critical columns: {missing_cols}. "
            f"Found columns: {list(df_raw.columns[:10])}..."
        )
    print(f"[Kaggle Ingestion] Schema validation PASSED (missing optional cols: {missing_cols})")

    # 2. Adapt Cell2Cell → canonical schema
    df_canonical = adapt_cell2cell_to_canonical(df_raw)
    print(f"[Kaggle Ingestion] Adapted to canonical schema: {list(df_canonical.columns)}")

    # 3. Standard DQ checks (same function used for synthetic data)
    df_valid, quality_report = validate_and_filter_raw_data(df_canonical)
    print(
        f"[Kaggle Ingestion] DQ Check: {quality_report['status']} | "
        f"Valid: {quality_report['valid_rows_passed']} | "
        f"Filtered: {quality_report['malformed_rows_filtered']}"
    )

    # 4. Imputation
    df_clean = clean_and_impute_missing(df_valid)

    # 5. Feature engineering (derived features)
    df_features = compute_derived_features(df_clean)

    # 6. Save dataset-specific parquet (immutable snapshot of this ingestion)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    kaggle_parquet_path = PROCESSED_DATA_DIR / "kaggle_features.parquet"
    df_features.to_parquet(kaggle_parquet_path, index=False)
    print(f"[Kaggle Ingestion] Saved Kaggle features to: {kaggle_parquet_path}")

    # 7. Also save to standard training path so training.py picks it up by default
    processed_parquet_path = PROCESSED_DATA_DIR / "customer_features.parquet"
    df_features.to_parquet(processed_parquet_path, index=False)

    # Save DQ report
    dq_report_path = PROCESSED_DATA_DIR / "dq_report.json"
    with open(dq_report_path, "w") as f:
        json.dump(quality_report, f, indent=2)

    # 8. Register in dataset registry with SHA-256
    try:
        registry = DatasetRegistry()
        registry.register_dataset(
            name=f"cell2cell_{raw_kaggle_path.stem}",
            path=raw_kaggle_path,
            source="kaggle",
            row_count=len(df_features),
            notes=f"Cell2Cell Kaggle dataset. Raw file: {raw_kaggle_path.name}",
        )
    except Exception as exc:
        print(f"[DatasetRegistry] Warning: Could not register Kaggle dataset: {exc}")

    # 9. Persist to database
    if db_path is not None and str(db_path).endswith(".db"):
        conn = sqlite3.connect(db_path)
        df_features.to_sql("customers", conn, if_exists="replace", index=False)
        conn.close()
    else:
        from backend.app.db.session import SessionLocal
        from backend.app.db.models.customer import Customer

        session = SessionLocal()
        try:
            session.query(Customer).delete()
            cust_records = df_features.to_dict(orient="records")
            for r in cust_records:
                # Only pass columns that match the Customer model
                valid_cols = {c.name for c in Customer.__table__.columns}
                filtered = {k: v for k, v in r.items() if k in valid_cols}
                session.add(Customer(**filtered))
            session.commit()
            print(f"[Kaggle Ingestion] Persisted {len(cust_records):,} customers to PostgreSQL")
        except Exception as e:
            session.rollback()
            print(f"[Kaggle Ingestion] Error persisting to PostgreSQL: {e}")
        finally:
            session.close()

    summary = {
        "status": "SUCCESS",
        "source": "kaggle",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "schedule_type": schedule_type,
        "rows_received": total_raw_rows,
        "rows_ingested": len(df_features),
        "malformed_rows_filtered": quality_report["malformed_rows_filtered"],
        "kaggle_parquet_output": str(kaggle_parquet_path),
        "parquet_output": str(processed_parquet_path),
        "database_output": str(db_path),
        "dq_report_path": str(dq_report_path),
        "quality_status": quality_report["status"],
        "raw_source_file": str(raw_kaggle_path),
    }
    print(f"[Kaggle Ingestion] Completed: {summary}")
    return summary


if __name__ == "__main__":
    run_batch_ingestion()
