"""SHAP Explainability Module (TICKET-206, TASK 13).

Generates per-customer and batch feature attributions using SHAP (SHapley Additive exPlanations),
with model-aware explainer selection, reliable human-readable feature mappings, and positive/negative risk drivers.
"""

from typing import Any
import numpy as np
import pandas as pd
import shap


# Reliable human-readable feature metadata and business formatting mapping
FEATURE_METADATA_MAP: dict[str, dict[str, Any]] = {
    "tenure_months": {
        "display_name": "Customer Tenure",
        "category": "Tenure & Loyalty",
        "formatter": lambda v: f"{int(float(v))} months" if v is not None and str(v) != "" else "N/A",
    },
    "monthly_charges": {
        "display_name": "Monthly Charges",
        "category": "Billing & Pricing",
        "formatter": lambda v: f"₹{float(v):,.2f}" if v is not None and str(v) != "" else "N/A",
    },
    "total_charges": {
        "display_name": "Total Charges",
        "category": "Billing & Pricing",
        "formatter": lambda v: f"₹{float(v):,.2f}" if v is not None and str(v) != "" else "N/A",
    },
    "support_calls_m1": {
        "display_name": "Customer Service Calls (Month 1)",
        "category": "Customer Support",
        "formatter": lambda v: f"{int(float(v))} calls" if v is not None and str(v) != "" else "0 calls",
    },
    "support_calls_m2": {
        "display_name": "Customer Service Calls (Month 2)",
        "category": "Customer Support",
        "formatter": lambda v: f"{int(float(v))} calls" if v is not None and str(v) != "" else "0 calls",
    },
    "support_calls_m3": {
        "display_name": "Customer Service Calls (Month 3)",
        "category": "Customer Support",
        "formatter": lambda v: f"{int(float(v))} calls" if v is not None and str(v) != "" else "0 calls",
    },
    "support_call_trend": {
        "display_name": "Support Call Trend (MoM)",
        "category": "Customer Support",
        "formatter": lambda v: f"{'+' if float(v) > 0 else ''}{int(float(v))} calls MoM" if v is not None and str(v) != "" else "0",
    },
    "call_minutes_m1": {
        "display_name": "Monthly Voice Minutes (Month 1)",
        "category": "Usage & Engagement",
        "formatter": lambda v: f"{float(v):.1f} mins" if v is not None and str(v) != "" else "0 mins",
    },
    "call_minutes_m2": {
        "display_name": "Voice Minutes (Month 2)",
        "category": "Usage & Engagement",
        "formatter": lambda v: f"{float(v):.1f} mins" if v is not None and str(v) != "" else "0 mins",
    },
    "call_minutes_m3": {
        "display_name": "Voice Minutes (Month 3)",
        "category": "Usage & Engagement",
        "formatter": lambda v: f"{float(v):.1f} mins" if v is not None and str(v) != "" else "0 mins",
    },
    "data_gb_m1": {
        "display_name": "Monthly Data Usage (Month 1)",
        "category": "Usage & Engagement",
        "formatter": lambda v: f"{float(v):.1f} GB" if v is not None and str(v) != "" else "0 GB",
    },
    "data_gb_m2": {
        "display_name": "Data Usage (Month 2)",
        "category": "Usage & Engagement",
        "formatter": lambda v: f"{float(v):.1f} GB" if v is not None and str(v) != "" else "0 GB",
    },
    "data_gb_m3": {
        "display_name": "Data Usage (Month 3)",
        "category": "Usage & Engagement",
        "formatter": lambda v: f"{float(v):.1f} GB" if v is not None and str(v) != "" else "0 GB",
    },
    "usage_drop_call_pct": {
        "display_name": "Voice Usage Drop (%)",
        "category": "Usage & Engagement",
        "formatter": lambda v: f"{float(v)*100:.1f}%" if v is not None and str(v) != "" else "0.0%",
    },
    "usage_drop_data_pct": {
        "display_name": "Data Usage Drop (%)",
        "category": "Usage & Engagement",
        "formatter": lambda v: f"{float(v)*100:.1f}%" if v is not None and str(v) != "" else "0.0%",
    },
    "contract_type": {
        "display_name": "Contract Type",
        "category": "Contract & Plan",
        "formatter": lambda v: str(v) if v is not None else "N/A",
    },
    "payment_method": {
        "display_name": "Payment Method",
        "category": "Billing & Pricing",
        "formatter": lambda v: str(v) if v is not None else "N/A",
    },
    "plan_tier": {
        "display_name": "Plan Tier",
        "category": "Contract & Plan",
        "formatter": lambda v: str(v) if v is not None else "N/A",
    },
    "region": {
        "display_name": "Service Region",
        "category": "Demographics",
        "formatter": lambda v: str(v) if v is not None else "N/A",
    },
    "recharge_count_m1": {
        "display_name": "Recharge Count (Month 1)",
        "category": "Billing & Pricing",
        "formatter": lambda v: f"{int(float(v))} recharges" if v is not None and str(v) != "" else "0",
    },
    "recharge_count_m2": {
        "display_name": "Recharge Count (Month 2)",
        "category": "Billing & Pricing",
        "formatter": lambda v: f"{int(float(v))} recharges" if v is not None and str(v) != "" else "0",
    },
    "recharge_count_m3": {
        "display_name": "Recharge Count (Month 3)",
        "category": "Billing & Pricing",
        "formatter": lambda v: f"{int(float(v))} recharges" if v is not None and str(v) != "" else "0",
    },
    "avg_monthly_recharges": {
        "display_name": "Average Monthly Recharges",
        "category": "Billing & Pricing",
        "formatter": lambda v: f"{float(v):.1f} / mo" if v is not None and str(v) != "" else "0",
    },
    "tenure_bucket": {
        "display_name": "Tenure Group",
        "category": "Tenure & Loyalty",
        "formatter": lambda v: str(v) if v is not None else "N/A",
    },
}

# In-memory explainer cache to avoid rebuilding explainer instances on every request
_EXPLAINER_CACHE: dict[int, Any] = {}


def get_human_readable_feature_info(raw_feature_name: str) -> tuple[str, str, str]:
    """Map raw or one-hot encoded feature names to (base_feature, display_name, category)."""
    clean_name = raw_feature_name.replace("cat__", "").replace("num__", "")

    # Direct match in metadata map
    if clean_name in FEATURE_METADATA_MAP:
        meta = FEATURE_METADATA_MAP[clean_name]
        return clean_name, meta["display_name"], meta["category"]

    # Check for one-hot encoded patterns: feature_category_val
    for base_feat, meta in FEATURE_METADATA_MAP.items():
        if clean_name.startswith(f"{base_feat}_"):
            cat_val = clean_name[len(base_feat) + 1 :]
            display_name = f"{meta['display_name']} ({cat_val})"
            return base_feat, display_name, meta["category"]

    # Fallback to readable title
    readable = clean_name.replace("_", " ").title()
    return clean_name, readable, "General"


def format_feature_value(base_feature: str, raw_value: Any) -> str:
    """Format customer's feature value with appropriate units and currency."""
    if raw_value is None or (isinstance(raw_value, float) and np.isnan(raw_value)):
        return "N/A"

    if base_feature in FEATURE_METADATA_MAP:
        try:
            return FEATURE_METADATA_MAP[base_feature]["formatter"](raw_value)
        except Exception:
            return str(raw_value)

    return str(raw_value)


def _get_or_create_explainer(classifier: Any, X_sample: np.ndarray) -> tuple[Any, float]:
    """Retrieve or create the appropriate SHAP explainer based on classifier type."""
    clf_id = id(classifier)
    if clf_id in _EXPLAINER_CACHE:
        return _EXPLAINER_CACHE[clf_id]

    cls_name = classifier.__class__.__name__.lower()
    try:
        if "tree" in cls_name or "forest" in cls_name or "boost" in cls_name:
            explainer = shap.TreeExplainer(classifier)
        elif "logistic" in cls_name or "linear" in cls_name:
            explainer = shap.LinearExplainer(classifier, X_sample)
        else:
            explainer = shap.Explainer(classifier.predict_proba, X_sample[:min(50, len(X_sample))])
    except Exception:
        # Robust fallback
        explainer = shap.Explainer(classifier.predict_proba, X_sample[:min(50, len(X_sample))])

    # Extract base value
    base_val = 0.50
    try:
        if hasattr(explainer, "expected_value"):
            ev = explainer.expected_value
            if isinstance(ev, (list, np.ndarray)):
                base_val = float(ev[1]) if len(ev) > 1 else float(ev[0])
            else:
                base_val = float(ev)
    except Exception:
        base_val = 0.50

    _EXPLAINER_CACHE[clf_id] = (explainer, base_val)
    return explainer, base_val


def compute_shap_explanations(
    model_pipeline: Any,
    X_df: pd.DataFrame,
    top_n: int = 5,
) -> list[dict[str, Any]]:
    """Generate per-customer SHAP feature importances with positive & negative churn drivers.

    Returns a list of structured explanation dictionaries per customer record.
    """
    if len(X_df) == 0:
        return []

    try:
        # Check and compute derived features if missing
        from ml_engine.pipelines.feature_engineering import compute_derived_features
        if "usage_drop_call_pct" not in X_df.columns and "call_minutes_m1" in X_df.columns:
            X_proc = compute_derived_features(X_df)
        else:
            X_proc = X_df.copy()

        # Extract preprocessor and classifier from Pipeline
        if hasattr(model_pipeline, "named_steps"):
            preprocessor = model_pipeline.named_steps.get("preprocessor")
            classifier = model_pipeline.named_steps.get("classifier")
            if preprocessor:
                X_trans = preprocessor.transform(X_proc)
                if hasattr(X_trans, "toarray"):
                    X_trans = X_trans.toarray()
                feature_names = preprocessor.get_feature_names_out()
            else:
                X_trans = X_proc.values
                feature_names = np.array(X_proc.columns)
        else:
            classifier = model_pipeline
            X_trans = X_proc.values
            feature_names = np.array(X_proc.columns)

        # Initialize / retrieve explainer
        explainer, base_val = _get_or_create_explainer(classifier, X_trans)

        try:
            shap_values = explainer.shap_values(X_trans)
        except Exception:
            # Fallback to general callable
            if hasattr(classifier, "predict_proba"):
                gen_expl = shap.Explainer(classifier.predict_proba, X_trans[: min(50, len(X_trans))])
                shap_values = gen_expl(X_trans[: len(X_trans)]).values
            else:
                raise ValueError("Model does not support probability prediction for SHAP.")

        # Handle multi-class / binary array shapes
        if isinstance(shap_values, list):
            sv = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        elif len(shap_values.shape) == 3:
            sv = shap_values[:, :, 1]
        else:
            sv = shap_values
    except Exception as e:
        # Graceful fallback: return UNAVAILABLE status records
        return [
            {
                "explanation_status": "UNAVAILABLE",
                "base_value": 0.50,
                "top_features": [],
                "top_positive_drivers": [],
                "top_negative_drivers": [],
                "all_drivers": [],
                "summary": f"Feature explanations unavailable: {str(e)}",
                "disclaimer": "Feature contribution explains the model's prediction; it does not prove causation.",
            }
            for _ in range(len(X_df))
        ]

    explanations = []
    for i in range(len(X_df)):
        customer_sv = sv[i]
        customer_row = X_df.iloc[i]

        # Build feature attribution records for all transformed features
        all_attributions = []
        for idx in range(len(feature_names)):
            raw_fname = str(feature_names[idx])
            base_feat, display_name, category = get_human_readable_feature_info(raw_fname)
            impact = float(customer_sv[idx])

            # Get customer's raw feature value if column exists in input
            raw_val = customer_row[base_feat] if base_feat in customer_row else None
            formatted_val = format_feature_value(base_feat, raw_val)

            # Convert numpy types to native python types for JSON serialization
            serializable_raw_val = None
            if raw_val is not None:
                if isinstance(raw_val, (np.integer, int)):
                    serializable_raw_val = int(raw_val)
                elif isinstance(raw_val, (np.floating, float)):
                    serializable_raw_val = None if np.isnan(raw_val) else float(raw_val)
                else:
                    serializable_raw_val = str(raw_val)

            all_attributions.append({
                "feature": raw_fname.replace("cat__", "").replace("num__", ""),
                "feature_name": base_feat,
                "display_name": display_name,
                "feature_value": formatted_val,
                "raw_value": serializable_raw_val,
                "importance": round(impact, 4),
                "contribution": round(impact, 4),
                "impact": "Increase" if impact > 0 else "Decrease",
                "direction": "INCREASES_CHURN" if impact > 0 else "DECREASES_CHURN",
                "effect": "Increases churn risk" if impact > 0 else "Reduces churn risk",
                "category": category,
            })

        # Sort all by absolute contribution magnitude for legacy top_features
        sorted_by_abs = sorted(all_attributions, key=lambda x: abs(x["contribution"]), reverse=True)
        top_features = sorted_by_abs[:top_n]

        # Filter and sort positive drivers (increasing churn risk)
        pos_drivers = [a for a in all_attributions if a["contribution"] > 0]
        pos_drivers = sorted(pos_drivers, key=lambda x: x["contribution"], reverse=True)[:top_n]

        # Filter and sort negative drivers / protective factors (reducing churn risk)
        neg_drivers = [a for a in all_attributions if a["contribution"] < 0]
        neg_drivers = sorted(neg_drivers, key=lambda x: abs(x["contribution"]), reverse=True)[:top_n]

        # Construct concise human-readable summary
        if pos_drivers and neg_drivers:
            summary = f"Risk is primarily elevated by {pos_drivers[0]['display_name']} ({pos_drivers[0]['feature_value']}), offset by protective factor {neg_drivers[0]['display_name']} ({neg_drivers[0]['feature_value']})."
        elif pos_drivers:
            summary = f"Risk is primarily driven by {pos_drivers[0]['display_name']} ({pos_drivers[0]['feature_value']})."
        elif neg_drivers:
            summary = f"Strong protective retention factor observed: {neg_drivers[0]['display_name']} ({neg_drivers[0]['feature_value']})."
        else:
            summary = "Model attributions indicate neutral feature contributions."

        explanations.append({
            "explanation_status": "AVAILABLE",
            "base_value": round(base_val, 4),
            "top_features": top_features,
            "top_positive_drivers": pos_drivers,
            "top_negative_drivers": neg_drivers,
            "all_drivers": sorted_by_abs[: max(10, top_n * 2)],
            "summary": summary,
            "disclaimer": "Feature contribution explains the model's prediction; it does not prove causation.",
        })

    return explanations

