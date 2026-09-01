"""# Feature Mapping Documentation (TASK-21)

## Overview

This document describes how raw dataset columns are mapped to the canonical feature schema used throughout the Telecom Churn Analysis Platform.

## Canonical Schema Definition

All datasets are transformed to this canonical schema before training:

```python
CATEGORICAL_FEATURES = [
    "plan_tier",           # Customer plan tier (Basic/Standard/Premium)
    "contract_type",       # Contract duration (Month-to-Month/One Year/Two Year)
    "payment_method",      # Payment method (Auto/Check/Credit Card/Electronic)
    "region",              # Geographic region (East/West/South/Central)
]

NUMERICAL_FEATURES = [
    "tenure_months",       # Months as customer (integer, ≥1)
    "monthly_charges",     # Monthly service charge (float, ₹)
    "total_charges",       # Total lifetime charges (float, ₹)
    "call_minutes_m1",     # Call minutes, period 1 (float)
    "call_minutes_m2",     # Call minutes, period 2 (float)
    "call_minutes_m3",     # Call minutes, period 3 (float)
    "data_gb_m1",          # Data usage, period 1 (float, GB)
    "data_gb_m2",          # Data usage, period 2 (float, GB)
    "data_gb_m3",          # Data usage, period 3 (float, GB)
    "recharge_count_m1",   # Recharges, period 1 (integer)
    "recharge_count_m2",   # Recharges, period 2 (integer)
    "recharge_count_m3",   # Recharges, period 3 (integer)
    "support_calls_m1",    # Support calls, period 1 (integer)
    "support_calls_m2",    # Support calls, period 2 (integer)
    "support_calls_m3",    # Support calls, period 3 (integer)
]

DERIVED_FEATURES = [
    "usage_drop_call_pct",     # % change in call minutes (m1→m3)
    "usage_drop_data_pct",     # % change in data usage (m1→m3)
    "support_call_trend",      # Trend: m1 vs m3 (up/flat/down)
    "avg_monthly_recharges",   # Average recharges across 3 periods
    "tenure_bucket",           # Tenure categorization (new/mid/loyal)
]

TARGET = "churn"               # Binary: 1=churned, 0=retained
```

## Dataset-Specific Mappings

### 1. Cell2Cell (Duke/Teradata Kaggle Dataset)

**Dataset Size**: 71,047 rows × 58 columns

**Mapping Rules**:

```
Cell2Cell Column          → Canonical Column          Transformation
─────────────────────────────────────────────────────────────────────
CustomerID               → customer_id                String conversion
Churn                    → churn                      "Yes"→1, else→0
TenureMonths             → tenure_months              Direct (integer)
MonthlyRevenue           → monthly_charges            Direct (float)
TotalRecurringCharge     → total_charges              Direct (float)

# Usage Proxies (call minutes)
MonthlyMinutes           → call_minutes_m1            Direct
OverageMinutes           → call_minutes_m2            Direct
RoamingCalls             → call_minutes_m3            Direct

# Data Usage Proxies
NumberofDataSets         → data_gb_m1                 Scale if needed
PercChangeRevenues       → data_gb_m2                 Normalized
(other usage cols)       → data_gb_m3                 Median impute

# Support Interaction Proxies
CustomerCareCalls        → support_calls_m1           Direct (integer)
RetentionCalls           → support_calls_m2           Direct (integer)
InboundCalls             → support_calls_m3           Direct (integer)

# Categorical (Defaulted/Derived)
(tenure-based)           → contract_type              Derived from tenure
(charges-based)          → plan_tier                  Derived from charges
(available in data)      → payment_method             Direct or mode-fill
(zip code)               → region                     Parsed or mode-fill
```

**Defensive Mapping**:
- Every column lookup is guarded: `if col in df.columns`
- Missing columns are imputed with sensible defaults
- Data types are coerced to canonical types
- Categorical values normalized (e.g., "Yes"/"yes"/"1" → 1)

**Example Code**:
```python
from ml_engine.pipelines.kaggle_adapter import adapt_cell2cell_to_canonical

df_raw = pd.read_csv("data/raw/cell2cell.csv")
df_canonical = adapt_cell2cell_to_canonical(df_raw)
```

### 2. IBM Telco Customer Churn (Kaggle)

**Dataset Size**: 7,043 rows × 21 columns

**Mapping Rules**:

```
Telco Column             → Canonical Column          Transformation
─────────────────────────────────────────────────────────────────────
customerID               → customer_id                String
Churn                    → churn                      "Yes"→1, else→0
tenure                   → tenure_months              Direct (integer)
MonthlyCharges           → monthly_charges            Direct (float)
TotalCharges             → total_charges              Direct (float)

# Usage Proxies (no native monthly breakdown in Telco)
(construct from charges) → call_minutes_m1            Derived
(construct from charges) → call_minutes_m2            Derived
(construct from charges) → call_minutes_m3            Derived

InternetType             → data_gb_m1                 Categorical→numeric
(derived)                → data_gb_m2                 Derived
(derived)                → data_gb_m3                 Derived

# Support Metrics
(tech support flag)      → support_calls_m1           Binary→count
(tech support flag)      → support_calls_m2           Binary→count
(tech support flag)      → support_calls_m3           Binary→count

# Categorical (Direct)
Contract                 → contract_type              Direct (mapping)
PaymentMethod            → payment_method            Direct or mode-fill
(from PhoneService)      → plan_tier                  Derived or default
(from address)           → region                     Parsed or default
```

**Adapter Module**: `ml_engine/pipelines/telco_adapter.py`

```python
from ml_engine.pipelines.telco_adapter import adapt_telco_to_canonical

df_raw = pd.read_csv("data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv")
df_canonical = adapt_telco_to_canonical(df_raw)
```

### 3. Synthetic Dataset (Built-in)

**Generation Method**: Procedural, matches canonical schema exactly

**Mapping**: None (already in canonical schema)

```python
from ml_engine.pipelines.synthetic_data_generator import save_synthetic_data

usage_path, logs_path = save_synthetic_data(n_samples=10000)
```

## Feature Engineering Pipeline

### 1. Schema Alignment (Adapter Layer)
- Raw columns renamed/imputed to match canonical names
- Data types coerced to canonical types
- Missing values filled with sensible defaults

### 2. Data Quality Validation (TICKET-103)
- Null percentage checks per column
- Range validation (tenure ≥1, charges ≥0)
- Churn ratio bounds (5-95%)
- Duplicate detection

### 3. Missing Value Imputation
```python
from ml_engine.pipelines.data_quality import clean_and_impute_missing

df_clean = clean_and_impute_missing(df_canonical)
```

- **Numerical**: Median imputation
- **Categorical**: Mode imputation ("Unknown" default)

### 4. Derived Feature Computation
```python
from ml_engine.pipelines.feature_engineering import compute_derived_features

df_features = compute_derived_features(df_clean)
```

**Derived Features**:

```python
# Usage Drop Percentage (call minutes)
usage_drop_call_pct = (
    (call_minutes_m1 - call_minutes_m3) / call_minutes_m1 * 100
)  # NaN safe

# Usage Drop Percentage (data)
usage_drop_data_pct = (
    (data_gb_m1 - data_gb_m3) / data_gb_m1 * 100
)  # NaN safe

# Support Call Trend (categorical: -1/0/+1)
support_call_trend = np.sign(support_calls_m3 - support_calls_m1)

# Average Monthly Recharges
avg_monthly_recharges = (
    recharge_count_m1 + recharge_count_m2 + recharge_count_m3
) / 3

# Tenure Bucket (categorical: "new"/"mid"/"loyal")
tenure_bucket = pd.cut(
    tenure_months,
    bins=[0, 12, 24, 100],
    labels=["new", "mid", "loyal"],
    include_lowest=True
)
```

### 5. Preprocessing & Scaling
```python
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), NUMERICAL_FEATURES + derived_numeric),
        ("cat", OneHotEncoder(sparse_output=False), CATEGORICAL_FEATURES),
    ]
)

X_scaled = preprocessor.fit_transform(df_features)
```

### 6. SMOTE (Training Set Only)
```python
from imblearn.over_sampling import SMOTE

smote = SMOTE(sampling_strategy=0.5, random_state=42)
X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
```

- Applied **only to training split** (prevents leakage)
- Sampling strategy: 0.5 (minority:majority ratio)

## Data Type Specifications

| Feature | Type | Range | Examples |
|---------|------|-------|----------|
| customer_id | str | N/A | "C123", "T4567" |
| churn | int | {0, 1} | 0 (retained), 1 (churned) |
| tenure_months | int | [1, 72] | 1, 12, 36, 60 |
| monthly_charges | float | [0, 10000] | 29.99, 65.50, 88.75 |
| total_charges | float | [0, 1000000] | 999.50, 15680.25 |
| call_minutes_m* | float | [0, ∞) | 100.5, 2500.0 |
| data_gb_m* | float | [0, ∞) | 0.0, 50.0, 200.0 |
| recharge_count_m* | int | [0, ∞) | 0, 1, 5, 12 |
| support_calls_m* | int | [0, ∞) | 0, 1, 3, 8 |
| usage_drop_*_pct | float | [-inf, inf] | -50.0, 0.0, 75.0 |
| support_call_trend | int | {-1, 0, 1} | -1, 0, 1 |
| avg_monthly_recharges | float | [0, ∞) | 0.0, 2.5, 4.0 |
| tenure_bucket | str | {new, mid, loyal} | "new", "loyal" |
| plan_tier | str | {Basic, Standard, Premium} | "Standard" |
| contract_type | str | {Month-to-Month, One Year, Two Year} | "One Year" |
| payment_method | str | {Auto, Check, Credit, Electronic} | "Auto" |
| region | str | {East, West, South, Central} | "East" |

## Validation Rules

### Schema Validation
```python
from ml_engine.pipelines.data_quality import validate_and_filter_raw_data

df_valid, report = validate_and_filter_raw_data(df_raw)
# Raises DataValidationError if critical columns missing
```

### Content Validation
- `tenure_months ≥ 1` (no zero tenure)
- `monthly_charges ≥ 0` (non-negative)
- `total_charges ≥ monthly_charges × tenure_months × 0.8` (sanity check)
- `churn ∈ {0, 1}` (binary)
- `customer_id` is unique and non-null

### Missing Value Limits
Per column:
- **Categorical**: ≤ 20% null
- **Numerical**: ≤ 10% null
- **Target (churn)**: 0% null

## Example: Full Feature Engineering Workflow

```python
import pandas as pd
from ml_engine.pipelines.kaggle_adapter import adapt_cell2cell_to_canonical
from ml_engine.pipelines.data_quality import (
    validate_and_filter_raw_data,
    clean_and_impute_missing,
)
from ml_engine.pipelines.feature_engineering import compute_derived_features
from ml_engine.config import PROCESSED_DATA_DIR

# 1. Load raw Cell2Cell data
df_raw = pd.read_csv("data/raw/cell2cell.csv")
print(f"Raw shape: {df_raw.shape}")

# 2. Adapt to canonical schema
df_canonical = adapt_cell2cell_to_canonical(df_raw)
print(f"Canonical shape: {df_canonical.shape}")

# 3. Validate schema and content
df_valid, report = validate_and_filter_raw_data(df_canonical)
print(f"Validation: {report['status']}")

# 4. Impute missing values
df_clean = clean_and_impute_missing(df_valid)
print(f"Clean shape: {df_clean.shape}")

# 5. Engineer derived features
df_features = compute_derived_features(df_clean)
print(f"Features shape: {df_features.shape}")

# 6. Save for training
output_path = PROCESSED_DATA_DIR / "cell2cell_features.parquet"
df_features.to_parquet(output_path, index=False)
```

## Troubleshooting

### Issue: "Missing required columns"
```
Error: DataValidationError: Critical Schema Violation: Missing required columns
→ Check that the dataset_adapter mapped all required columns
→ Verify input CSV has expected Cell2Cell/Telco column names
```

### Issue: "Churn ratio out of bounds"
```
Error: Data Quality Report: Invalid churn distribution
→ Ensure target churn rate is between 5% and 95%
→ Check that churn column is correctly mapped
```

### Issue: "Tenure is zero"
```
Error: tenure_months < 1 detected
→ Adapter automatically clips to ≥1
→ Check if source data has invalid tenure values
```

### Issue: "Data leakage detected"
```
Warning: Possible data leakage in feature set
→ Verify that churn target is not included in features
→ Check derived features don't use future information
```

## References

- [ml_engine/config.py](../ml_engine/config.py) - Canonical schema definition
- [ml_engine/pipelines/kaggle_adapter.py](../ml_engine/pipelines/kaggle_adapter.py) - Cell2Cell mapping
- [ml_engine/pipelines/telco_adapter.py](../ml_engine/pipelines/telco_adapter.py) - Telco mapping
- [ml_engine/pipelines/feature_engineering.py](../ml_engine/pipelines/feature_engineering.py) - Derived features
- [docs/DATASET.md](../docs/DATASET.md) - Dataset integration overview
