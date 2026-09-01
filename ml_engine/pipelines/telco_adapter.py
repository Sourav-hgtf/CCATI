"""IBM Telco Customer Churn Dataset Adapter (TASK-21 Extension).

Maps the IBM Watson / Blastchar Telco Customer Churn dataset columns
(kaggle: blastchar/telco-customer-churn) to the canonical project schema.

Dataset: WA_Fn-UseC_-Telco-Customer-Churn.csv
Shape  : 7,043 rows × 21 columns
Churn  : ~26.5% (Yes/No string)

Column mapping (Telco → Canonical)
────────────────────────────────────────────────────────────────
customerID       → customer_id
Churn            → churn          (Yes/No → 1/0)
tenure           → tenure_months
MonthlyCharges   → monthly_charges
TotalCharges     → total_charges  (contains whitespace → numeric)
Contract         → contract_type  (values already canonical)
PaymentMethod    → payment_method (values already canonical)
InternetService  → plan_tier      (proxy: DSL/Fiber/No → Basic/Premium/No plan)

Columns WITHOUT a direct canonical equivalent are imputed:
─ call_minutes_m1/m2/m3  : from MonthlyCharges-scaled proxy + tenure decay
─ data_gb_m1/m2/m3       : from InternetService tier proxy
─ recharge_count_m1/m2/m3: imputed 0 (prepaid model N/A for Telco postpaid)
─ support_calls_m1/m2/m3 : from TechSupport / OnlineSecurity binary flags proxy
─ region                 : imputed "Unknown" (not in dataset)
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ── Critical columns required to identify this as the IBM Telco dataset ─────
_TELCO_CRITICAL_COLS: list[str] = [
    "customerID",
    "Churn",
    "tenure",
    "MonthlyCharges",
    "Contract",
]

# ── Direct rename map ────────────────────────────────────────────────────────
_DIRECT_RENAME: dict[str, str] = {
    "customerID":     "customer_id",
    "Churn":          "churn",
    "tenure":         "tenure_months",
    "MonthlyCharges": "monthly_charges",
    "TotalCharges":   "total_charges",
    "Contract":       "contract_type",
    "PaymentMethod":  "payment_method",
}


def validate_telco_schema(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Check whether the DataFrame looks like the IBM Telco dataset.

    Returns:
        (is_valid, missing_critical_cols)
    """
    missing = [c for c in _TELCO_CRITICAL_COLS if c not in df.columns]
    is_valid = len(missing) == 0  # All 5 critical cols must be present
    return is_valid, missing


def _map_internet_to_plan_tier(internet_service: pd.Series) -> pd.Series:
    """Map InternetService values to canonical plan_tier."""
    mapping = {
        "Fiber optic": "Postpaid Premium",
        "DSL":         "Postpaid Standard",
        "No":          "Prepaid Basic",
    }
    return internet_service.map(mapping).fillna("Postpaid Standard")


def _derive_support_calls(df: pd.DataFrame) -> pd.Series:
    """Derive support_calls_m1 proxy from TechSupport + OnlineSecurity flags."""
    has_tech = df.get("TechSupport", pd.Series("No", index=df.index)).map(
        lambda v: 1 if str(v).lower() in {"yes"} else 0
    )
    has_security = df.get("OnlineSecurity", pd.Series("No", index=df.index)).map(
        lambda v: 0 if str(v).lower() in {"yes"} else 1  # No security = more support calls
    )
    # Estimate 1–4 support calls based on service issue signals
    base = (has_security + has_tech).clip(0, 2)
    return base


def adapt_telco_to_canonical(df: pd.DataFrame) -> pd.DataFrame:
    """Map an IBM Telco DataFrame to the project's canonical feature schema.

    Steps
    -----
    1. Rename direct-mapping columns.
    2. Coerce churn to int (Yes→1, No→0).
    3. Coerce TotalCharges (contains whitespace strings) to float.
    4. Map InternetService → plan_tier.
    5. Synthesise call_minutes, data_gb, recharge, support proxies.
    6. Impute region = "Unknown".
    7. Add identity placeholder columns.
    8. Return only canonical + identity columns.

    Args:
        df: Raw IBM Telco DataFrame.

    Returns:
        DataFrame with canonical schema ready for validate_and_filter_raw_data().
    """
    out = df.copy()

    # ── 1. Rename direct columns ────────────────────────────────────────────
    rename_map = {k: v for k, v in _DIRECT_RENAME.items() if k in out.columns}
    out = out.rename(columns=rename_map)

    # ── 2. Churn → int ──────────────────────────────────────────────────────
    if "churn" in out.columns:
        out["churn"] = (
            out["churn"].astype(str).str.strip().str.lower()
            .map({"yes": 1, "no": 0, "1": 1, "0": 0, "1.0": 1, "0.0": 0})
            .fillna(0)
            .astype(int)
        )
    else:
        out["churn"] = 0

    # ── 3. TotalCharges: strip whitespace, coerce to float ──────────────────
    if "total_charges" in out.columns:
        out["total_charges"] = pd.to_numeric(
            out["total_charges"].astype(str).str.strip(), errors="coerce"
        )
        # Fill new-customer blanks (tenure=0) with MonthlyCharges
        zero_mask = out["total_charges"].isna()
        if "monthly_charges" in out.columns:
            out.loc[zero_mask, "total_charges"] = out.loc[zero_mask, "monthly_charges"]
        out["total_charges"] = out["total_charges"].fillna(0.0)

    # ── 4. plan_tier from InternetService ───────────────────────────────────
    if "InternetService" in out.columns:
        out["plan_tier"] = _map_internet_to_plan_tier(out["InternetService"])
    elif "plan_tier" not in out.columns:
        out["plan_tier"] = "Postpaid Standard"

    # ── 5. Numerical proxies ─────────────────────────────────────────────────
    # Ensure scalar numerics exist
    for col in ["tenure_months", "monthly_charges", "total_charges"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
        else:
            out[col] = 0.0

    out["tenure_months"] = out["tenure_months"].clip(lower=1).round().astype(int)

    # call_minutes proxies: scale monthly_charges → minutes (industry ≈ 1 USD/min avg)
    mc = out["monthly_charges"]
    out["call_minutes_m1"] = (mc * 6.5).round(1)           # most recent month
    out["call_minutes_m2"] = (mc * 6.5 * 1.05).round(1)   # slight growth trend
    out["call_minutes_m3"] = (mc * 6.5 * 1.10).round(1)   # oldest month

    # data_gb proxies: based on InternetService tier
    internet = df.get("InternetService", pd.Series("DSL", index=df.index))
    data_base = internet.map({"Fiber optic": 80.0, "DSL": 30.0, "No": 2.0}).fillna(30.0)
    out["data_gb_m1"] = data_base.round(1)
    out["data_gb_m2"] = (data_base * 1.02).round(1)
    out["data_gb_m3"] = (data_base * 1.05).round(1)

    # recharge_count: Telco is postpaid — set to 1 per month (autopay)
    out["recharge_count_m1"] = 1
    out["recharge_count_m2"] = 1
    out["recharge_count_m3"] = 1

    # support_calls: derive from TechSupport / security flags
    support_proxy = _derive_support_calls(df)
    out["support_calls_m1"] = (support_proxy + 1).clip(upper=5).astype(int)
    out["support_calls_m2"] = support_proxy.clip(upper=4).astype(int)
    out["support_calls_m3"] = (support_proxy - 1).clip(lower=0, upper=3).astype(int)

    # ── 6. Categorical fallbacks ─────────────────────────────────────────────
    if "payment_method" not in out.columns:
        out["payment_method"] = "Electronic check"
    if "contract_type" not in out.columns:
        out["contract_type"] = "Month-to-month"
    out["region"] = "Unknown"

    # Normalise whitespace
    for col in ["plan_tier", "contract_type", "payment_method", "region"]:
        out[col] = out[col].fillna("Unknown").astype(str).str.strip()

    # ── 7. Identity placeholders ─────────────────────────────────────────────
    out["name"]  = out.get("gender", pd.Series("Unknown", index=out.index)).astype(str)
    out["phone"] = ""
    out["email"] = ""

    # ── 8. Select and return canonical columns only ──────────────────────────
    canonical = [
        "name", "phone", "email",
        "customer_id", "churn",
        "tenure_months", "monthly_charges", "total_charges",
        "call_minutes_m1", "call_minutes_m2", "call_minutes_m3",
        "data_gb_m1", "data_gb_m2", "data_gb_m3",
        "recharge_count_m1", "recharge_count_m2", "recharge_count_m3",
        "support_calls_m1", "support_calls_m2", "support_calls_m3",
        "plan_tier", "contract_type", "payment_method", "region",
    ]
    return out[[c for c in canonical if c in out.columns]].copy()


def get_telco_mapping_report() -> dict[str, str]:
    """Return the Telco → canonical column mapping for documentation."""
    return dict(_DIRECT_RENAME)
