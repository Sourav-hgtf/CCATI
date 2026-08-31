# ML Engine Component — Telecom Churn Platform

Scikit-learn classification, SHAP explainability, and K-Means segmentation engine.

## Directory Structure
- `pipelines/ingestion.py` — Batch ingestion pipeline (24-month log retention enforcement)
- `pipelines/feature_engineering.py` — Derived features (usage deltas, rolling averages, tenure buckets)
- `pipelines/training.py` — Stratified split, SMOTE oversampling (training fold only), Logistic Regression, Random Forest, XGBoost
- `pipelines/evaluation.py` — Recall, Precision, ROC-AUC, PR-AUC, Confusion Matrix
- `pipelines/explainability.py` — SHAP feature attributions per customer
- `pipelines/clustering.py` — K-Means clustering (filtered for Churn Prob >= 0.5) and PCA 2D coordinates
- `registry/model_registry.py` — Artifact storage (.joblib) and metadata versioning
