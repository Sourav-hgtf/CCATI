"""Test Business Decision Engine logic."""

from business_engine.risk_scoring import calculate_risk_scores, compute_clv
from business_engine.roi_calculator import calculate_retention_roi
from business_engine.recommendations import get_recommended_action


def test_clv_computation():
    clv = compute_clv(monthly_charges=500.0, tenure_months=24)
    assert clv == 6000.0


def test_risk_score_calculation():
    scores = calculate_risk_scores(
        churn_probabilities=[0.85, 0.20],
        monthly_charges=[800.0, 300.0],
        tenures=[12, 36]
    )
    assert len(scores) == 2
    assert scores[0]["risk_tier"] == "High"
    assert scores[1]["risk_tier"] == "Low"
    assert scores[0]["priority_score"] > scores[1]["priority_score"]


def test_roi_calculator():
    roi = calculate_retention_roi(clv=10000.0, churn_prob=0.8, action_cost=100.0, expected_save_rate=0.4)
    assert roi["expected_saved_revenue"] == 3200.0
    assert roi["net_saved_revenue"] == 3100.0
    assert roi["roi_pct"] == 3100.0


def test_recommendation_engine():
    rec = get_recommended_action(
        risk_tier="High",
        churn_prob=0.8,
        clv=12000.0,
        support_calls_m1=4
    )
    assert rec["action_code"] == "proactive_support"
    assert "roi_details" in rec
