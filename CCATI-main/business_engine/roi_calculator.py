"""ROI Calculator Module (TICKET-402).

Estimates retention cost vs. expected revenue saved per recommended retention action.
"""

from typing import Any


def calculate_retention_roi(
    clv: float,
    churn_prob: float,
    action_cost: float,
    expected_save_rate: float
) -> dict[str, float]:
    """Calculate projected revenue saved and net ROI percentage for a retention action.
    
    Formula:
      Expected Saved Revenue = CLV * churn_prob * expected_save_rate
      Net Saved Revenue = Expected Saved Revenue - action_cost
      ROI % = (Net Saved Revenue / action_cost) * 100
    """
    expected_saved_revenue = round(clv * churn_prob * expected_save_rate, 2)
    net_saved = round(expected_saved_revenue - action_cost, 2)
    
    if action_cost > 0:
        roi_pct = round((net_saved / action_cost) * 100, 1)
    else:
        roi_pct = 0.0

    return {
        "action_cost": float(action_cost),
        "expected_saved_revenue": float(expected_saved_revenue),
        "net_saved_revenue": float(net_saved),
        "roi_pct": float(roi_pct),
    }
