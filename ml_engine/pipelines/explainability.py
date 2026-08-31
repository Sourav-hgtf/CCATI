"""SHAP Explainability Module (TICKET-206).

Generates per-customer feature attribution values using SHAP (SHapley Additive exPlanations).
"""

from typing import Any
import numpy as np
import pandas as pd
import shap


def compute_shap_explanations(
    model_pipeline: Any,
    X_df: pd.DataFrame,
    top_n: int = 5
) -> list[dict[str, Any]]:
    """Generate per-customer SHAP feature importances.
    
    Returns a list of dictionaries per customer record containing top contributing features.
    """
    # Extract classifier from Pipeline if passed as Pipeline
    if hasattr(model_pipeline, "named_steps"):
        preprocessor = model_pipeline.named_steps.get("preprocessor")
        classifier = model_pipeline.named_steps.get("classifier")
        if preprocessor:
            X_trans = preprocessor.transform(X_df)
            if hasattr(X_trans, "toarray"):
                X_trans = X_trans.toarray()
            # Feature names post-preprocessing
            feature_names = preprocessor.get_feature_names_out()
        else:
            X_trans = X_df.values
            feature_names = np.array(X_df.columns)
    else:
        classifier = model_pipeline
        X_trans = X_df.values
        feature_names = np.array(X_df.columns)

    # Initialize appropriate SHAP Explainer
    try:
        explainer = shap.TreeExplainer(classifier)
        shap_values = explainer.shap_values(X_trans)
    except Exception:
        # Fallback to Kernel or Explainer
        explainer = shap.Explainer(classifier.predict_proba, X_trans[:50])
        shap_values = explainer(X_trans[: len(X_trans)]).values

    # Handle multi-class / binary array shapes
    if isinstance(shap_values, list):
        # Minority class (churn=1) shap values
        sv = shap_values[1] if len(shap_values) > 1 else shap_values[0]
    elif len(shap_values.shape) == 3:
        sv = shap_values[:, :, 1]
    else:
        sv = shap_values

    explanations = []
    for i in range(len(X_df)):
        customer_sv = sv[i]
        # Sort indices by absolute SHAP impact
        top_indices = np.argsort(np.abs(customer_sv))[::-1][:top_n]
        
        feature_attributions = []
        for idx in top_indices:
            fname = str(feature_names[idx]).replace("cat__", "").replace("num__", "")
            impact = float(customer_sv[idx])
            feature_attributions.append({
                "feature": fname,
                "importance": round(impact, 4),
                "direction": "INCREASES_CHURN" if impact > 0 else "DECREASES_CHURN",
            })
            
        explanations.append({
            "top_features": feature_attributions
        })

    return explanations
