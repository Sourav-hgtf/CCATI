# Data Storage Directory — Telecom Churn Platform

Local data assets and model registry storage.

## Subdirectories
- `raw/` — Ingested source CSV/Parquet files (Enforced 24-month retention window)
- `processed/` — Engineered feature Parquet tables (`customer_features.parquet`)
- `database/` — SQLite/PostgreSQL system of record database (`telecom_churn.db`)
- `models/` — Persisted model artifacts (`.joblib`) and registry metadata JSON
