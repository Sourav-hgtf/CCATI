"""# Dataset Integration Documentation (TASK-21)

## Overview

This document describes the dataset integration architecture for TASK-21, including:
- Kaggle dataset acquisition
- Raw dataset storage and versioning
- Schema validation and data quality checks
- Feature mapping to canonical schema
- Dataset lifecycle management

## Datasets Supported

### 1. Cell2Cell (Kaggle)
- **Source**: `aryafar/cell2cell-telecom-churn`
- **Records**: 71,047
- **Features**: 58
- **Target**: Binary churn indicator
- **License**: Kaggle Terms of Service

### 2. IBM Telco Customer Churn (Kaggle)
- **Source**: `blastchar/telco-customer-churn`
- **Records**: 7,043
- **Features**: 21
- **Target**: Binary churn indicator
- **License**: Kaggle Terms of Service

### 3. Synthetic (Built-in)
- **Source**: Auto-generated
- **Records**: Variable (default 10,000)
- **Features**: Matches canonical schema
- **Target**: Synthetic churn probability

## Data Directory Structure

```
data/
├── raw/                          # Immutable raw datasets
│   ├── cell2cell_*.csv
│   ├── WA_Fn-UseC_-Telco-Customer-Churn.csv
│   ├── customer_usage_raw.parquet
│   ├── customer_call_logs_raw.csv
│   └── dataset_registry.json
├── interim/                       # Cleaned, validated intermediate data
│   ├── cell2cell_validated.parquet
│   └── telco_validated.parquet
├── processed/                     # Feature-engineered, ready for training
│   ├── customer_features.parquet
│   ├── dq_report.json
│   ├── train_features.parquet
│   ├── test_features.parquet
│   └── feature_metadata.json
├── validation/                    # Validation results and reports
│   ├── cell2cell_validation.json
│   ├── telco_validation.json
│   └── data_leakage_report.json
└── metadata/                      # Dataset and model metadata
    ├── cell2cell_metadata.json
    ├── telco_metadata.json
    └── feature_statistics.json
```

## Dataset Acquisition

### Secure Kaggle Integration

Credentials are handled securely via:
1. **Environment Variables** (recommended for CI/CD):
   ```bash
   export KAGGLE_USERNAME=<your_username>
   export KAGGLE_KEY=<your_api_key>
   ```

2. **Kaggle Configuration File** (for local development):
   ```
   ~/.kaggle/kaggle.json
   ```

**DO NOT** hardcode credentials in Python files.

### Download via Python API

```python
from ml_engine.pipelines.kaggle_download import download_cell2cell_dataset

# Download Cell2Cell dataset
dataset_path = download_cell2cell_dataset(output_path="data/raw/")
```

## Dataset Versioning

Each raw dataset is registered in `data/raw/dataset_registry.json`:

```json
{
  "cell2cell_v1": {
    "name": "cell2cell_v1",
    "source": "kaggle",
    "path": "/path/to/cell2cell_*.csv",
    "sha256": "abc123def456...",
    "row_count": 71047,
    "registered_at": "2026-09-01T12:00:00Z",
    "notes": "Cell2Cell Kaggle dataset, v1"
  }
}
```

### SHA-256 Hashing

Every raw dataset file is hashed using SHA-256 to:
- Detect file corruption
- Ensure reproducibility
- Track dataset versions
- Enable audit trails

```python
from ml_engine.pipelines.dataset_registry import DatasetRegistry

registry = DatasetRegistry()
registry.register_dataset(
    name="cell2cell_v1",
    path="data/raw/cell2cell.csv",
    source="kaggle",
    row_count=71047,
    notes="Initial Cell2Cell ingestion"
)
```

## Canonical Feature Schema

All datasets are mapped to a **canonical schema** before training:

### Categorical Features
- `plan_tier`: Customer plan (Basic, Standard, Premium)
- `contract_type`: Contract duration (Month-to-Month, One Year, Two Year)
- `payment_method`: Payment type (Auto, Check, Credit Card, etc.)
- `region`: Geographic region

### Numerical Features
- `tenure_months`: Months as customer (≥1)
- `monthly_charges`: Monthly service charge (₹)
- `total_charges`: Total lifetime charge (₹)
- Usage metrics (call_minutes, data_gb, recharge_count, support_calls) per 3 periods

### Derived Features
- `usage_drop_call_pct`: % change in call minutes
- `usage_drop_data_pct`: % change in data usage
- `support_call_trend`: Trend in support interactions
- `avg_monthly_recharges`: Average recharges
- `tenure_bucket`: Tenure categorization

### Target Variable
- `churn`: Binary (0=retained, 1=churned)

## Data Quality Validation (TICKET-103)

All raw data undergoes validation:

### Schema Validation
- Column presence check
- Data type verification
- Primary key (customer_id) uniqueness

### Content Validation
- Null percentage per column
- Range validation (tenure ≥0, charges ≥0)
- Churn ratio bounds (5-95%)
- Duplicate detection

### Data Leakage Detection
- Target (churn) presence in features
- Leakage indicator patterns
- Temporal data ordering issues

### Output Report
```json
{
  "total_rows_received": 71047,
  "valid_rows_passed": 70891,
  "malformed_rows_filtered": 156,
  "null_counts": {...},
  "schema_validation": "PASSED",
  "status": "PASSED_WITH_WARNINGS"
}
```

## Training/Test Split

- **Train**: 80% of validated data
- **Test**: 20% of validated data
- **Stratification**: On churn target
- **Random state**: 42 (reproducibility)
- **SMOTE**: Applied only to training set to prevent leakage

## Feature Engineering Pipeline

1. **Missing Value Imputation**:
   - Numerical: Median imputation
   - Categorical: Mode imputation

2. **Outlier Detection**:
   - Numerical features: ±3σ bounds

3. **Scaling**:
   - StandardScaler for numerical features
   - OneHotEncoder for categorical features

4. **Derived Features**:
   - Computed from raw features per schema

5. **SMOTE (Training Only)**:
   - Oversampling ratio: 0.5
   - Applied to training split only

## Model Training Integration

```python
from ml_engine.pipelines.ingestion import run_batch_ingestion
from ml_engine.pipelines.training import train_churn_classification_pipeline

# Ingest Kaggle data
ingestion_report = run_batch_ingestion(
    source="kaggle",
    raw_kaggle_path="data/raw/cell2cell.csv"
)

# Train models with data lineage
training_report = train_churn_classification_pipeline(
    data_source="kaggle"
)
```

## Metadata Tracking

### Dataset Metadata (`data/metadata/<dataset>_metadata.json`)
```json
{
  "dataset_name": "cell2cell_v1",
  "source": "kaggle",
  "sha256": "abc123...",
  "row_count": 71047,
  "feature_count": 58,
  "churn_distribution": {0: 53200, 1: 17847},
  "ingestion_timestamp": "2026-09-01T12:00:00Z",
  "schema_version": "1.0"
}
```

### Feature Statistics (`data/metadata/feature_statistics.json`)
```json
{
  "tenure_months": {
    "mean": 32.4,
    "std": 24.5,
    "min": 1,
    "max": 72
  },
  ...
}
```

## Usage Workflows

### Workflow 1: Fresh Kaggle Ingestion

```bash
# Step 1: Set Kaggle credentials
export KAGGLE_USERNAME=<username>
export KAGGLE_KEY=<api_key>

# Step 2: Run ingestion with Kaggle source
python -c "
from ml_engine.pipelines.ingestion import run_batch_ingestion
report = run_batch_ingestion(source='kaggle')
print(report)
"

# Step 3: Verify dataset registry
cat data/raw/dataset_registry.json
```

### Workflow 2: Model Training with Kaggle Data

```python
from ml_engine.pipelines.ingestion import run_batch_ingestion
from ml_engine.pipelines.training import train_churn_classification_pipeline

# Ingest and train
run_batch_ingestion(source='kaggle', raw_kaggle_path='data/raw/cell2cell.csv')
training_report = train_churn_classification_pipeline(data_source='kaggle')

print(f\"Best model: {training_report['best_model']}\")
```

## Performance Considerations

- **Raw dataset storage**: 5-50 MB (uncompressed CSV)
- **Processed features**: 10-100 MB (Parquet)
- **Model training time**: 5-30 minutes (CPU)
- **Inference latency**: <100 ms per prediction

## Reproducibility

To ensure reproducible training across environments:

1. **Pin dataset version**: Use SHA-256 hash
2. **Pin feature engineering**: Use `feature_metadata.json`
3. **Pin model registry**: Use model version ID
4. **Pin random seed**: RANDOM_STATE=42

```python
# Complete reproducible workflow
from ml_engine.pipelines.dataset_registry import DatasetRegistry

registry = DatasetRegistry()
dataset_version = registry.get_by_name('cell2cell_v1')

# Training uses this specific dataset version
train_churn_classification_pipeline(
    data_source='kaggle',  # Ensures metadata tracking
    processed_data_path='data/processed/customer_features.parquet'
)
```

## Security & Compliance

- **Credentials**: Never hardcoded, always via env vars or ~/.kaggle/
- **Immutable storage**: Raw data in `data/raw/` never overwritten
- **Audit trail**: Dataset registry tracks all versions
- **Data privacy**: No PII stored except customer_id
- **License compliance**: All datasets used per Kaggle Terms

## Troubleshooting

### Kaggle Download Fails
```
Error: Kaggle credentials not found
→ Set KAGGLE_USERNAME and KAGGLE_KEY environment variables
```

### Schema Validation Fails
```
Error: Critical Schema Violation: Missing required columns
→ Ensure dataset_adapter.py correctly maps your dataset
```

### SMOTE Out-of-Memory
```
Error: Memory error during SMOTE
→ Reduce dataset size or increase available RAM
```

## References

- [Kaggle API Documentation](https://github.com/Kaggle/kaggle-api)
- [Cell2Cell Dataset](https://www.kaggle.com/aryafar/cell2cell-telecom-churn)
- [IBM Telco Dataset](https://www.kaggle.com/blastchar/telco-customer-churn)
- [Feature Engineering Best Practices](../docs/FEATURE_MAPPING.md)
