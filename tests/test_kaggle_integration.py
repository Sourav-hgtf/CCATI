"""TASK-21: Kaggle Dataset Integration Tests.

Tests the Cell2Cell adapter, dataset registry, ingestion pipeline (kaggle mode),
training pipeline (data_source traceability), and admin API endpoints.

All tests use synthetic Cell2Cell-shaped data — no real Kaggle download is required.
The existing synthetic ingestion path is tested to confirm it is unaffected.
"""

from pathlib import Path
import tempfile
import json
import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures: synthetic data shaped like Cell2Cell
# ──────────────────────────────────────────────────────────────────────────────

def _make_cell2cell_df(n: int = 200) -> pd.DataFrame:
    """Generate a minimal Cell2Cell-shaped DataFrame for testing."""
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "CustomerID":           [f"C2C-{i:06d}" for i in range(n)],
        "Churn":                rng.integers(0, 2, size=n),
        "TenureMonths":         rng.integers(1, 72, size=n).astype(float),
        "MonthlyRevenue":       rng.uniform(30, 150, size=n).round(2),
        "TotalRecurringCharge": rng.uniform(30, 150, size=n).round(2),
        "MonthlyMinutes":       rng.uniform(100, 1000, size=n).round(1),
        "OverageMinutes":       rng.uniform(0, 200, size=n).round(1),
        "RoamingCalls":         rng.integers(0, 20, size=n).astype(float),
        "CustomerCareCalls":    rng.integers(0, 10, size=n),
        "RetentionCalls":       rng.integers(0, 5, size=n),
        "InboundCalls":         rng.integers(0, 3, size=n),
        "NumberofDataSets":     rng.uniform(1, 50, size=n).round(1),
        "PercChangeRevenues":   rng.uniform(-0.5, 0.5, size=n).round(3),
    })


@pytest.fixture(scope="module")
def cell2cell_df() -> pd.DataFrame:
    return _make_cell2cell_df()


@pytest.fixture(scope="module")
def cell2cell_csv_path(cell2cell_df) -> Path:
    """Write a Cell2Cell CSV to a temp file and yield the path."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        cell2cell_df.to_csv(f, index=False)
        return Path(f.name)


@pytest.fixture(scope="module")
def registry_tmp_dir() -> Path:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


# ──────────────────────────────────────────────────────────────────────────────
# 1 & 2: Schema Validation
# ──────────────────────────────────────────────────────────────────────────────

def test_cell2cell_schema_validation_passes_with_valid_data(cell2cell_df):
    """Schema validator accepts a well-formed Cell2Cell DataFrame."""
    from ml_engine.pipelines.kaggle_adapter import validate_cell2cell_schema
    is_valid, missing = validate_cell2cell_schema(cell2cell_df)
    assert is_valid, f"Expected valid schema, got missing: {missing}"


def test_cell2cell_schema_validation_fails_on_missing_critical_columns():
    """Schema validator rejects a DataFrame that is missing most critical columns."""
    from ml_engine.pipelines.kaggle_adapter import validate_cell2cell_schema
    bad_df = pd.DataFrame({"SomeColumn": [1, 2, 3], "Another": [4, 5, 6]})
    is_valid, missing = validate_cell2cell_schema(bad_df)
    assert not is_valid
    assert len(missing) >= 4  # at least 4 of 6 critical cols missing


# ──────────────────────────────────────────────────────────────────────────────
# 3 & 4: Adapter Produces Canonical Schema
# ──────────────────────────────────────────────────────────────────────────────

def test_adapter_maps_to_canonical_schema(cell2cell_df):
    """Adapter renames Cell2Cell columns to canonical names."""
    from ml_engine.pipelines.kaggle_adapter import adapt_cell2cell_to_canonical
    result = adapt_cell2cell_to_canonical(cell2cell_df)
    assert "customer_id" in result.columns
    assert "churn" in result.columns
    assert "tenure_months" in result.columns
    assert "monthly_charges" in result.columns
    assert "CustomerID" not in result.columns  # original should be gone


def test_adapter_output_has_all_canonical_features(cell2cell_df):
    """Adapter produces all canonical columns required by the training pipeline."""
    from ml_engine.pipelines.kaggle_adapter import adapt_cell2cell_to_canonical
    from ml_engine.config import NUMERICAL_FEATURES, CATEGORICAL_FEATURES

    result = adapt_cell2cell_to_canonical(cell2cell_df)
    required = NUMERICAL_FEATURES + CATEGORICAL_FEATURES + ["customer_id", "churn"]
    missing = [c for c in required if c not in result.columns]
    assert missing == [], f"Adapter output is missing canonical columns: {missing}"


def test_adapter_churn_column_binary_values(cell2cell_df):
    """Adapter ensures churn column contains only 0 and 1 integer values."""
    from ml_engine.pipelines.kaggle_adapter import adapt_cell2cell_to_canonical
    result = adapt_cell2cell_to_canonical(cell2cell_df)
    unique_churn = set(result["churn"].unique())
    assert unique_churn.issubset({0, 1}), f"Unexpected churn values: {unique_churn}"
    assert result["churn"].dtype in (int, "int64", "int32")


# ──────────────────────────────────────────────────────────────────────────────
# 5 & 6: Adapter handles edge cases
# ──────────────────────────────────────────────────────────────────────────────

def test_adapter_handles_string_churn_values():
    """Adapter correctly maps string churn values ('Yes'/'No') to 1/0."""
    from ml_engine.pipelines.kaggle_adapter import adapt_cell2cell_to_canonical
    df = _make_cell2cell_df(50)
    df["Churn"] = ["Yes" if v == 1 else "No" for v in df["Churn"]]
    result = adapt_cell2cell_to_canonical(df)
    assert set(result["churn"].unique()).issubset({0, 1})


def test_adapter_handles_missing_optional_columns():
    """Adapter imputes canonical values for Cell2Cell columns that are absent."""
    from ml_engine.pipelines.kaggle_adapter import adapt_cell2cell_to_canonical
    # Minimal Cell2Cell — only the three most critical columns
    df = pd.DataFrame({
        "CustomerID": [f"X{i}" for i in range(30)],
        "Churn":      [0] * 30,
        "MonthlyRevenue": np.random.uniform(30, 100, 30),
        "TenureMonths": np.random.randint(1, 60, 30).astype(float),
        "CustomerCareCalls": np.random.randint(0, 5, 30),
    })
    result = adapt_cell2cell_to_canonical(df)
    # These should all be imputed to default values
    assert "plan_tier" in result.columns
    assert "contract_type" in result.columns
    assert "payment_method" in result.columns
    assert "region" in result.columns
    assert result["region"].iloc[0] == "Unknown"
    assert result["payment_method"].iloc[0] == "Electronic Check"


# ──────────────────────────────────────────────────────────────────────────────
# 7 & 8: Dataset Registry
# ──────────────────────────────────────────────────────────────────────────────

def test_dataset_registry_registers_dataset_with_sha256(cell2cell_csv_path, registry_tmp_dir):
    """DatasetRegistry records SHA-256, row count, and source correctly."""
    from ml_engine.pipelines.dataset_registry import DatasetRegistry, compute_file_sha256

    registry = DatasetRegistry(registry_file=registry_tmp_dir / "registry.json")
    entry = registry.register_dataset(
        name="test_c2c",
        path=cell2cell_csv_path,
        source="kaggle",
        row_count=200,
        notes="test entry",
    )

    assert entry["sha256"] != ""
    assert len(entry["sha256"]) == 64  # SHA-256 hex = 64 chars
    assert entry["source"] == "kaggle"
    assert entry["row_count"] == 200
    assert "registered_at" in entry

    # Verify SHA-256 matches direct computation
    assert entry["sha256"] == compute_file_sha256(cell2cell_csv_path)


def test_dataset_registry_lists_registered_datasets(registry_tmp_dir):
    """DatasetRegistry.list_datasets() returns all entries."""
    from ml_engine.pipelines.dataset_registry import DatasetRegistry

    reg_file = registry_tmp_dir / "registry_list.json"
    registry = DatasetRegistry(registry_file=reg_file)

    # Register two entries (path doesn't need to exist for listing test)
    fake_path = registry_tmp_dir / "fake.csv"
    fake_path.write_text("a,b\n1,2\n")

    registry.register_dataset("ds_a", fake_path, "synthetic", 100)
    registry.register_dataset("ds_b", fake_path, "kaggle", 5000)

    datasets = registry.list_datasets()
    names = {d["name"] for d in datasets}
    assert "ds_a" in names
    assert "ds_b" in names
    assert len(datasets) == 2


def test_dataset_registry_verify_integrity(cell2cell_csv_path, registry_tmp_dir):
    """DatasetRegistry.verify_integrity() returns True when file is unchanged."""
    from ml_engine.pipelines.dataset_registry import DatasetRegistry

    reg_file = registry_tmp_dir / "registry_integrity.json"
    registry = DatasetRegistry(registry_file=reg_file)
    registry.register_dataset("integrity_test", cell2cell_csv_path, "kaggle", 200)

    assert registry.verify_integrity("integrity_test") is True


# ──────────────────────────────────────────────────────────────────────────────
# 9 & 10: Ingestion Pipeline — Kaggle mode
# ──────────────────────────────────────────────────────────────────────────────

def test_ingestion_kaggle_source_produces_parquet(cell2cell_csv_path):
    """Kaggle ingestion produces kaggle_features.parquet and customer_features.parquet."""
    import tempfile
    from ml_engine.pipelines.ingestion import run_batch_ingestion
    from ml_engine.config import PROCESSED_DATA_DIR

    summary = run_batch_ingestion(
        source="kaggle",
        raw_kaggle_path=cell2cell_csv_path,
        db_path=None,
    )

    assert summary["status"] == "SUCCESS"
    assert summary["source"] == "kaggle"
    assert summary["rows_ingested"] > 0

    # Both parquet files must exist after ingestion
    assert Path(summary["kaggle_parquet_output"]).exists()
    assert Path(summary["parquet_output"]).exists()


def test_ingestion_kaggle_source_runs_dq_checks(cell2cell_csv_path):
    """Kaggle ingestion runs standard DQ checks and reports quality status."""
    from ml_engine.pipelines.ingestion import run_batch_ingestion

    summary = run_batch_ingestion(
        source="kaggle",
        raw_kaggle_path=cell2cell_csv_path,
        db_path=None,
    )

    assert summary["quality_status"] in {"PASSED", "PASSED_WITH_WARNINGS"}
    assert "malformed_rows_filtered" in summary


def test_ingestion_kaggle_raises_on_missing_file():
    """Kaggle ingestion raises ValueError when the CSV path does not exist."""
    from ml_engine.pipelines.ingestion import run_batch_ingestion

    with pytest.raises(ValueError, match="not found"):
        run_batch_ingestion(
            source="kaggle",
            raw_kaggle_path=Path("/nonexistent/path/fake.csv"),
            db_path=None,
        )


def test_ingestion_kaggle_raises_on_none_path():
    """Kaggle ingestion raises ValueError when raw_kaggle_path is None."""
    from ml_engine.pipelines.ingestion import run_batch_ingestion

    with pytest.raises(ValueError, match="required"):
        run_batch_ingestion(source="kaggle", raw_kaggle_path=None, db_path=None)


# ──────────────────────────────────────────────────────────────────────────────
# 11: Synthetic path is unaffected
# ──────────────────────────────────────────────────────────────────────────────

def test_ingestion_synthetic_source_unaffected_by_kaggle_code():
    """Synthetic ingestion path works exactly as before — Kaggle code does not interfere."""
    import tempfile
    from ml_engine.pipelines.ingestion import run_batch_ingestion

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        summary = run_batch_ingestion(
            source="synthetic",
            db_path=db_path,
            schedule_type="test",
        )

    assert summary["status"] == "SUCCESS"
    assert summary["source"] == "synthetic"
    assert summary["rows_ingested"] > 0


# ──────────────────────────────────────────────────────────────────────────────
# 12: Training pipeline data_source traceability
# ──────────────────────────────────────────────────────────────────────────────

def test_training_pipeline_records_data_source_in_metadata(cell2cell_csv_path):
    """Training pipeline stores data_source in model registry hyperparameters."""
    import tempfile
    from ml_engine.pipelines.ingestion import run_batch_ingestion
    from ml_engine.pipelines.training import train_churn_classification_pipeline
    from ml_engine.registry.model_registry import ModelRegistry

    # Generate an imbalanced Cell2Cell CSV (~25% churn) for SMOTE to work correctly.
    # Real Cell2Cell has ~14% churn; our 200-row fixture is nearly 50/50 which
    # makes SMOTE refuse to oversample (minority already >= 80% of majority).
    rng = np.random.default_rng(99)
    n = 500
    imbalanced_df = pd.DataFrame({
        "CustomerID":           [f"C2C-{i:06d}" for i in range(n)],
        "Churn":                (rng.random(n) < 0.25).astype(int),   # ~25% churn
        "TenureMonths":         rng.integers(1, 72, size=n).astype(float),
        "MonthlyRevenue":       rng.uniform(30, 150, size=n).round(2),
        "TotalRecurringCharge": rng.uniform(30, 150, size=n).round(2),
        "MonthlyMinutes":       rng.uniform(100, 1000, size=n).round(1),
        "OverageMinutes":       rng.uniform(0, 200, size=n).round(1),
        "RoamingCalls":         rng.integers(0, 20, size=n).astype(float),
        "CustomerCareCalls":    rng.integers(0, 10, size=n),
        "RetentionCalls":       rng.integers(0, 5, size=n),
        "InboundCalls":         rng.integers(0, 3, size=n),
        "NumberofDataSets":     rng.uniform(1, 50, size=n).round(1),
        "PercChangeRevenues":   rng.uniform(-0.5, 0.5, size=n).round(3),
    })

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        imbalanced_df.to_csv(f, index=False)
        imbalanced_csv = Path(f.name)

    # Ingest the imbalanced Kaggle data so customer_features.parquet is populated
    run_batch_ingestion(
        source="kaggle",
        raw_kaggle_path=imbalanced_csv,
        db_path=None,
    )

    # Train with kaggle data_source tag
    result = train_churn_classification_pipeline(
        promote_best=True,
        data_source="kaggle",
    )

    assert result["status"] == "SUCCESS"
    assert result["data_source"] == "kaggle"
    assert result["best_model_name"] is not None

    # Check the model registry persisted the data_source
    registry = ModelRegistry()
    info = registry.get_active_model_info()
    assert info["hyperparameters"].get("data_source") == "kaggle"


# ──────────────────────────────────────────────────────────────────────────────
# 13 & 14: Admin API endpoint auth guards
# ──────────────────────────────────────────────────────────────────────────────

def test_admin_kaggle_ingest_endpoint_requires_auth():
    """POST /admin/training/kaggle-ingest returns 401 without token."""
    response = client.post(
        "/api/v1/admin/training/kaggle-ingest",
        json={"kaggle_csv_path": "data/raw/cell2cell_churn.csv"},
    )
    assert response.status_code == 401


def test_admin_retrain_endpoint_requires_auth():
    """POST /admin/training/retrain returns 401 without token."""
    response = client.post(
        "/api/v1/admin/training/retrain",
        json={"data_source": "synthetic"},
    )
    assert response.status_code == 401


def test_admin_dataset_registry_endpoint_requires_auth():
    """GET /admin/training/dataset-registry returns 401 without token."""
    response = client.get("/api/v1/admin/training/dataset-registry")
    assert response.status_code == 401


def test_admin_retrain_rejects_non_admin_role(analyst_headers):
    """POST /admin/training/retrain returns 403 for Analyst role."""
    response = client.post(
        "/api/v1/admin/training/retrain",
        json={"data_source": "synthetic"},
        headers=analyst_headers,
    )
    assert response.status_code == 403


def test_admin_dataset_registry_accessible_by_admin(admin_headers):
    """GET /admin/training/dataset-registry returns 200 for Admin role."""
    response = client.get(
        "/api/v1/admin/training/dataset-registry",
        headers=admin_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert "datasets" in body
    assert "total" in body


def test_admin_retrain_rejects_invalid_data_source(admin_headers):
    """POST /admin/training/retrain returns 400 for an unknown data_source."""
    response = client.post(
        "/api/v1/admin/training/retrain",
        json={"data_source": "invalid_source"},
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert "data_source" in response.json()["detail"].lower()
