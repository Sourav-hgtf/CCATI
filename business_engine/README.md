# Business Decision Engine — Telecom Churn Platform

Priority risk scoring, ROI calculator, and targeted retention recommendation rule engine.

## Directory Structure
- `risk_scoring.py` — CLV calculation (`Monthly_Revenue * Expected_Remaining_Tenure`) and priority scores
- `roi_calculator.py` — Action cost vs expected saved revenue estimation
- `recommendations.py` — Risk tier + segment profile action lookup engine
- `rules_config.yaml` — Configurable action costs, save rates, and business rules
