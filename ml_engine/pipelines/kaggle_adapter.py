"""Cell2Cell Kaggle Dataset Adapter (TASK-21).

Maps the Cell2Cell (Duke University / Teradata) Kaggle telecom churn dataset
columns to the canonical feature schema used throughout this project.

The adapter is **defensive by design**: every column lookup is guarded with
``if col in df.columns`` so the code handles different Cell2Cell versions
(58-column, 71k-row and related variants) without crashing.

Canonical schema (from ml_engine/config.py)
-------------------------------------------
Categorical : plan_tier, contract_type, payment_method, region
Numerical   : tenure_months, monthly_charges, total_charges,
              call_minutes_m1/m2/m3, data_gb_m1/m2/m3,
              recharge_count_m1/m2/m3, support_calls_m1/m2/m3
Target      : churn  (int, 1=churned 0=retained)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Critical columns required to identify this as a Cell2Cell-family dataset.
# At least one of these *must* be present.
# ---------------------------------------------------------------------------
_C2C_CRITICAL_COLS: list[str] = [
    "CustomerID",
    "Churn",
    "MonthlyRevenue",
    "TenureMonths",
    "MonthlyMinutes",
    "CustomerCareCalls",
]

# ---------------------------------------------------------------------------
# Mapping: Cell2Cell column → canonical column
# ---------------------------------------------------------------------------
_COL_MAP: dict[str, str] = {
    "CustomerID":            "customer_id",
    "Churn":                 "churn",
    "TenureMonths":          "tenure_months",
    "MonthlyRevenue":        "monthly_charges",
    "TotalRecurringCharge":  "total_charges",
    # Usage proxies
    "MonthlyMinutes":        "call_minutes_m1",
    "OverageMinutes":        "call_minutes_m2",
    "RoamingCalls":          "call_minutes_m3",
    "NumberofDataSets":      "data_gb_m1",
    "PercChangeRevenues":    "data_gb_m2",
    # Support proxies
    "CustomerCareCalls":     "support_calls_m1",
    "RetentionCalls":        "support_calls_m2",
    "InboundCalls":          "support_calls_m3",
}

# All canonical columns needed downstream (must be present after mapping)
_CANONICAL_REQUIRED: list[str] = [
    "customer_id",
    "churn",
    "tenure_months",
    "monthly_charges",
    "total_charges",
    "call_minutes_m1",
    "call_minutes_m2",
    "call_minutes_m3",
    "data_gb_m1",
    "data_gb_m2",
    "data_gb_m3",
    "recharge_count_m1",
    "recharge_count_m2",
    "recharge_count_m3",
    "support_calls_m1",
    "support_calls_m2",
    "support_calls_m3",
    "plan_tier",
    "contract_type",
    "payment_method",
    "region",
]


def validate_cell2cell_schema(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Check whether the DataFrame looks like a Cell2Cell dataset.

    Validates that at least three of the six critical columns are present
    (so the adapter can produce a meaningful canonical frame).

    Returns:
        (is_valid, missing_critical_cols)
    """
    missing = [c for c in _C2C_CRITICAL_COLS if c not in df.columns]
    # Require at least 3 of 6 critical columns to be present
    found = len(_C2C_CRITICAL_COLS) - len(missing)
    is_valid = found >= 3
    return is_valid, missing


def _derive_contract_type_from_tenure(tenure_months: pd.Series) -> pd.Series:
    """Impute contract_type bucket from tenure as a reasonable default."""
    def _bucket(t: float) -> str:
        if t <= 12:
            return "Month-to-Month"
        elif t <= 24:
            return "One Year"
        else:
            return "Two Year"
    return tenure_months.apply(lambda t: _bucket(t) if pd.notna(t) else "Month-to-Month")


def adapt_cell2cell_to_canonical(df: pd.DataFrame) -> pd.DataFrame:
    """Map a Cell2Cell DataFrame to the project's canonical feature schema.

    Steps
    -----
    1. Rename mapped columns (guarded — only renames what exists).
    2. Impute missing canonical columns with sensible defaults.
    3. Coerce data types to match the canonical schema.
    4. Add placeholder identity columns (name, phone, email) for DB compat.
    5. Return DataFrame containing *exactly* the canonical columns.

    Args:
        df: Raw Cell2Cell DataFrame (any version, 58–78 columns typical).

    Returns:
        DataFrame with canonical schema, ready for ``validate_and_filter_raw_data()``.
    """
    out = df.copy()

    # ------------------------------------------------------------------
    # 1. Rename known Cell2Cell columns → canonical names
    # ------------------------------------------------------------------
    rename_map = {c2c: canon for c2c, canon in _COL_MAP.items() if c2c in out.columns}
    out = out.rename(columns=rename_map)

    # ------------------------------------------------------------------
    # 2. customer_id — ensure string, fill missing with synthetic IDs
    # ------------------------------------------------------------------
    if "customer_id" in out.columns:
        out["customer_id"] = out["customer_id"].astype(str).str.strip()
    else:
        out["customer_id"] = [f"C2C-{i:06d}" for i in range(len(out))]

    # ------------------------------------------------------------------
    # 3. churn — map Yes/True/1 → 1, anything else → 0
    # ------------------------------------------------------------------
    if "churn" in out.columns:
        churn_raw = out["churn"].astype(str).str.strip().str.lower()
        out["churn"] = churn_raw.map(
            lambda v: 1 if v in {"1", "yes", "true", "1.0"} else 0
        ).astype(int)
    else:
        out["churn"] = 0

    # ------------------------------------------------------------------
    # 4. Numerical columns — coerce to float, fill NaN with 0
    # ------------------------------------------------------------------
    num_proxies = [
        "tenure_months", "monthly_charges", "total_charges",
        "call_minutes_m1", "call_minutes_m2", "call_minutes_m3",
        "data_gb_m1", "data_gb_m2", "data_gb_m3",
        "recharge_count_m1", "recharge_count_m2", "recharge_count_m3",
        "support_calls_m1", "support_calls_m2", "support_calls_m3",
    ]
    for col in num_proxies:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
        else:
            out[col] = 0.0

    # tenure_months must be ≥ 1 to avoid downstream division errors
    out["tenure_months"] = out["tenure_months"].clip(lower=1)

    # total_charges: if missing or zero, derive from tenure × monthly
    zero_total = out["total_charges"] == 0.0
    if zero_total.any():
        out.loc[zero_total, "total_charges"] = (
            out.loc[zero_total, "tenure_months"] * out.loc[zero_total, "monthly_charges"]
        )

    # data_gb_m3: impute from median of m1 if completely absent/zero
    if out["data_gb_m3"].sum() == 0.0:
        median_data = out["data_gb_m1"].median()
        out["data_gb_m3"] = median_data if not np.isnan(median_data) else 1.0

    # Scale call_minutes_m3 (roaming proxy) to minutes range if very small
    if out["call_minutes_m3"].max() < 50:
        out["call_minutes_m3"] = out["call_minutes_m3"] * 10.0

    # Integer columns
    int_cols = [
        "tenure_months", "recharge_count_m1", "recharge_count_m2",
        "recharge_count_m3", "support_calls_m1", "support_calls_m2",
        "support_calls_m3",
    ]
    for col in int_cols:
        out[col] = out[col].round().astype(int)

    # ------------------------------------------------------------------
    # 5. Categorical columns — impute if absent
    # ------------------------------------------------------------------
    if "plan_tier" not in out.columns:
        # Derive from monthly_charges quartile
        q = out["monthly_charges"].quantile([0.33, 0.66])
        def _plan(v: float) -> str:
            if v <= q[0.33]:
                return "Prepaid Basic"
            elif v <= q[0.66]:
                return "Postpaid Standard"
            else:
                return "Postpaid Premium"
        out["plan_tier"] = out["monthly_charges"].apply(_plan)

    if "contract_type" not in out.columns:
        out["contract_type"] = _derive_contract_type_from_tenure(out["tenure_months"])

    if "payment_method" not in out.columns:
        out["payment_method"] = "Electronic Check"

    if "region" not in out.columns:
        out["region"] = "Unknown"

    # Normalise any string nulls
    for col in ["plan_tier", "contract_type", "payment_method", "region"]:
        out[col] = out[col].fillna("Unknown").astype(str).str.strip()

    # ------------------------------------------------------------------
    # 6. Identity placeholders (required by DB schema / ingestion)
    # ------------------------------------------------------------------
    if "name" not in out.columns:
        out["name"] = "Kaggle Customer"
    if "phone" not in out.columns:
        out["phone"] = ""
    if "email" not in out.columns:
        out["email"] = ""

    # ------------------------------------------------------------------
    # 7. Return only canonical columns (+ identity cols)
    # ------------------------------------------------------------------
    identity_cols = ["name", "phone", "email"]
    keep = identity_cols + _CANONICAL_REQUIRED
    return out[[c for c in keep if c in out.columns]].copy()


def get_cell2cell_mapping_report() -> dict[str, str]:
    """Return the Cell2Cell → canonical column mapping for documentation."""
    return dict(_COL_MAP)
