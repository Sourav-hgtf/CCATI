"""Risk Scoring Module (TICKET-401).

Combines ML churn probability with Customer Lifetime Value (CLV) into a composite priority score.
"""

from typing import Any
import numpy as np
import pandas as pd


def compute_clv(monthly_charges: float, tenure_months: int) -> float:
    """Compute Customer Lifetime Value (CLV) projection.
    
    Formula: CLV = monthly_charges * expected_remaining_tenure_months
    """
    expected_remaining_tenure_months = max(6, 24 - tenure_months) if tenure_months < 24 else 12
    return round(monthly_charges * expected_remaining_tenure_months, 2)


def calculate_risk_scores(
    churn_probabilities: np.ndarray,
    monthly_charges: np.ndarray | list[float],
    tenures: np.ndarray | list[int]
) -> list[dict[str, Any]]:
    """Compute risk tiers, CLV, and composite priority scores for subscribers."""
    results = []
    
    clvs = [compute_clv(mc, t) for mc, t in zip(monthly_charges, tenures)]
    max_clv = max(clvs) if max(clvs) > 0 else 1.0

    for prob, clv in zip(churn_probabilities, clvs):
        norm_clv = clv / max_clv
        
        # Priority score formula: exponential weight on churn probability * CLV factor
        raw_score = (prob ** 1.2) * (0.4 + 0.6 * norm_clv) * 100
        priority_score = min(100.0, round(float(raw_score), 1))

        if prob >= 0.70:
            risk_tier = "High"
        elif prob >= 0.35:
            risk_tier = "Medium"
        else:
            risk_tier = "Low"

        results.append({
            "churn_probability": round(float(prob), 4),
            "clv": float(clv),
            "priority_score": priority_score,
            "risk_tier": risk_tier,
        })

    return results
