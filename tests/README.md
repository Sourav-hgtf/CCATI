# Test Suite — Telecom Churn Platform

Pytest suite covering ML pipelines, business rules, RBAC security, and API endpoints.

## Directory Structure
- `ml_engine/` — Tests for SMOTE training isolation, evaluation metrics, SHAP, and clustering
- `business_engine/` — Tests for CLV (`Monthly_Revenue * Remaining_Tenure`), risk priority scoring, and ROI calculations
- `backend/` — Tests for FastAPI endpoints, PII masking, and RBAC guards
- `integration/` — End-to-end batch scoring pipeline tests

## Running Tests
```bash
pytest
```
