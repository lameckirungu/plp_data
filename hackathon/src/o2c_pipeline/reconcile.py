"""Reconciliation: join loading -> dispatch -> invoice -> payment and
quantify exactly where the order-to-cash cycle leaks revenue.

Every loading is valued at what it *should* be worth (volume x the
product's ex-depot price) and then debited across five mutually
exclusive leakage categories, so the categories always sum to total
leakage with no double counting:

  1. dispatch_capture_gap -- loaded, but no dispatch record exists at all.
     The product may have left the depot, but with nothing to
     reconcile against it can never legitimately be billed.
  2. shrinkage              -- dispatched volume is materially below
     loaded volume (physical loss in transit, beyond normal metering
     variance).
  3. billing_gap            -- confirmed dispatch, but no invoice was
     ever raised against it. The purest order-to-cash leak: product
     shipped, revenue never billed.
  4. underbilling            -- invoiced, but for less volume than was
     actually dispatched.
  5. collections_gap        -- invoiced correctly, but payment is
     partial or entirely outstanding.

Cancelled dispatches are excluded from every bucket -- they are a
legitimate business outcome, not a leak.
"""

import pandas as pd

from o2c_pipeline.config import (
    DEFAULT_UNIT_PRICE_KES,
    MAX_INVOICE_LAG_DAYS,
    MAX_PAYMENT_LAG_DAYS,
    SHRINKAGE_ALERT_THRESHOLD_PCT,
)

LEAKAGE_CATEGORIES = [
    "dispatch_capture_gap_kes",
    "shrinkage_kes",
    "billing_gap_kes",
    "underbilling_kes",
    "collections_gap_kes",
]


def _aggregate_invoices_with_payments(invoices: pd.DataFrame, payments: pd.DataFrame) -> pd.DataFrame:
    payment_agg = payments.groupby("invoice_id").agg(
        amount_paid_kes=("amount_paid_kes", "sum"),
        payment_date=("payment_date", "max"),
        payment_count=("payment_id", "count"),
    ).reset_index()

    inv = invoices.merge(payment_agg, on="invoice_id", how="left")
    inv["amount_paid_kes"] = inv["amount_paid_kes"].fillna(0.0)
    inv["collections_gap_kes"] = (inv["amount_kes"] - inv["amount_paid_kes"]).clip(lower=0)
    # An empty (or all-NaN) invoices/payments frame merges to an object-dtype
    # date column, not datetime64 -- coerce explicitly so .dt never blows up
    # on the edge case of zero invoiced/paid rows (e.g. an all-cancelled batch).
    inv["invoice_date"] = pd.to_datetime(inv["invoice_date"])
    inv["payment_date"] = pd.to_datetime(inv["payment_date"])
    inv["payment_lag_days"] = (inv["payment_date"] - inv["invoice_date"]).dt.days

    dispatch_level = inv.groupby("dispatch_id").agg(
        invoice_count=("invoice_id", "count"),
        volume_invoiced_litres=("volume_invoiced_litres", "sum"),
        invoiced_amount_kes=("amount_kes", "sum"),
        paid_amount_kes=("amount_paid_kes", "sum"),
        collections_gap_kes=("collections_gap_kes", "sum"),
        unit_price_kes=("unit_price_kes", "mean"),
        invoice_date=("invoice_date", "min"),
        payment_lag_days=("payment_lag_days", "max"),
    ).reset_index()
    return dispatch_level


def reconcile(cleaned: dict) -> pd.DataFrame:
    loadings = cleaned["loading_events"]
    dispatches = cleaned["dispatch_events"]
    invoices = cleaned["invoices"]
    payments = cleaned["payments"]

    dispatch_invoice_agg = _aggregate_invoices_with_payments(invoices, payments)

    base = loadings.merge(
        dispatches[["dispatch_id", "loading_id", "volume_dispatched_litres", "dispatch_ts", "status"]],
        on="loading_id",
        how="left",
    )
    merged = base.merge(dispatch_invoice_agg, on="dispatch_id", how="left")

    # An empty (or all-unmatched) right-hand side merges in as object dtype,
    # not float64/int64 -- coerce every numeric column pulled in from either
    # join so later arithmetic and .loc assignment never trip a dtype error
    # on the edge case of zero dispatches/invoices (e.g. an all-cancelled run).
    numeric_cols = [
        "volume_dispatched_litres", "invoice_count", "volume_invoiced_litres",
        "invoiced_amount_kes", "paid_amount_kes", "collections_gap_kes",
        "unit_price_kes", "payment_lag_days",
    ]
    for col in numeric_cols:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")

    default_price = merged["product"].map(DEFAULT_UNIT_PRICE_KES)
    merged["expected_revenue_kes"] = merged["volume_loaded_litres"] * default_price

    is_no_dispatch = merged["dispatch_id"].isna()
    is_cancelled = merged["status"] == "Cancelled"
    is_dispatched = merged["status"] == "Dispatched"
    is_invoiced = merged["invoice_count"].fillna(0) > 0

    # Same empty/all-NaN-merge dtype hazard as in _aggregate_invoices_with_payments.
    merged["invoice_date"] = pd.to_datetime(merged["invoice_date"])
    merged["dispatch_ts"] = pd.to_datetime(merged["dispatch_ts"])
    merged["invoice_lag_days"] = (merged["invoice_date"] - merged["dispatch_ts"]).dt.days

    # 1. dispatch capture gap
    merged["dispatch_capture_gap_kes"] = 0.0
    merged.loc[is_no_dispatch, "dispatch_capture_gap_kes"] = (
        merged.loc[is_no_dispatch, "volume_loaded_litres"] * default_price[is_no_dispatch]
    )

    # 2. shrinkage (only meaningful once dispatch is confirmed)
    shrinkage_litres = (merged["volume_loaded_litres"] - merged["volume_dispatched_litres"]).clip(lower=0)
    shrinkage_pct = (shrinkage_litres / merged["volume_loaded_litres"]) * 100
    material_shrinkage = is_dispatched & (shrinkage_pct > SHRINKAGE_ALERT_THRESHOLD_PCT)
    merged["shrinkage_litres"] = 0.0
    merged["shrinkage_kes"] = 0.0
    merged.loc[material_shrinkage, "shrinkage_litres"] = shrinkage_litres[material_shrinkage]
    merged.loc[material_shrinkage, "shrinkage_kes"] = (
        shrinkage_litres[material_shrinkage] * default_price[material_shrinkage]
    )

    # 3. billing gap
    billing_gap_mask = is_dispatched & ~is_invoiced
    merged["billing_gap_kes"] = 0.0
    merged.loc[billing_gap_mask, "billing_gap_kes"] = (
        merged.loc[billing_gap_mask, "volume_dispatched_litres"] * default_price[billing_gap_mask]
    )

    # 4. underbilling
    underbilled_litres = (merged["volume_dispatched_litres"] - merged["volume_invoiced_litres"]).clip(lower=0)
    underbilling_mask = is_dispatched & is_invoiced & (underbilled_litres > 0)
    valuation_price = merged["unit_price_kes"].fillna(default_price)
    merged["underbilling_litres"] = 0.0
    merged["underbilling_kes"] = 0.0
    merged.loc[underbilling_mask, "underbilling_litres"] = underbilled_litres[underbilling_mask]
    merged.loc[underbilling_mask, "underbilling_kes"] = (
        underbilled_litres[underbilling_mask] * valuation_price[underbilling_mask]
    )

    # 5. collections gap (already computed at dispatch level; zero out where not invoiced)
    merged["collections_gap_kes"] = merged["collections_gap_kes"].fillna(0.0)
    merged.loc[~is_invoiced, "collections_gap_kes"] = 0.0

    merged["total_leakage_kes"] = merged[LEAKAGE_CATEGORIES].sum(axis=1)
    merged.loc[is_cancelled, LEAKAGE_CATEGORIES + ["total_leakage_kes"]] = 0.0

    merged["collected_revenue_kes"] = merged["paid_amount_kes"].fillna(0.0)
    merged["late_invoice_flag"] = merged["invoice_lag_days"] > MAX_INVOICE_LAG_DAYS
    merged["late_payment_flag"] = merged["payment_lag_days"] > MAX_PAYMENT_LAG_DAYS
    merged["is_exception"] = (merged["total_leakage_kes"] > 1.0) & ~is_cancelled

    def dominant_category(row):
        if row["total_leakage_kes"] <= 1.0:
            return "none"
        values = {c: row[c] for c in LEAKAGE_CATEGORIES}
        return max(values, key=values.get).replace("_kes", "")

    merged["leakage_category"] = merged.apply(dominant_category, axis=1)

    return merged


def multi_invoice_exceptions(cleaned: dict) -> pd.DataFrame:
    """Dispatches billed on more than one invoice document -- a double-
    billing / audit-trail exception, surfaced separately from the KES
    leakage buckets above since it is a control failure, not a revenue
    loss per se."""
    invoices = cleaned["invoices"]
    counts = invoices.groupby("dispatch_id")["invoice_id"].agg(list)
    flagged = counts[counts.apply(len) > 1].reset_index()
    flagged.columns = ["dispatch_id", "invoice_ids"]
    return flagged


def summarize_by(reconciled: pd.DataFrame, group_col: str) -> pd.DataFrame:
    agg = reconciled.groupby(group_col).agg(
        loadings=("loading_id", "count"),
        expected_revenue_kes=("expected_revenue_kes", "sum"),
        collected_revenue_kes=("collected_revenue_kes", "sum"),
        total_leakage_kes=("total_leakage_kes", "sum"),
        **{c: (c, "sum") for c in LEAKAGE_CATEGORIES},
    ).reset_index()
    agg["leakage_pct_of_expected"] = 100 * agg["total_leakage_kes"] / agg["expected_revenue_kes"]
    return agg.sort_values("total_leakage_kes", ascending=False)


def overall_summary(reconciled: pd.DataFrame) -> dict:
    total_expected = reconciled["expected_revenue_kes"].sum()
    total_leakage = reconciled["total_leakage_kes"].sum()
    total_collected = reconciled["collected_revenue_kes"].sum()
    by_category = {c: float(reconciled[c].sum()) for c in LEAKAGE_CATEGORIES}
    n_days = 45  # simulation window; see scripts/generate_synthetic_data.py NUM_DAYS
    return {
        "total_loadings": int(len(reconciled)),
        "total_expected_revenue_kes": float(total_expected),
        "total_collected_revenue_kes": float(total_collected),
        "total_leakage_kes": float(total_leakage),
        "leakage_pct_of_expected_revenue": float(100 * total_leakage / total_expected),
        "leakage_by_category_kes": by_category,
        "exception_count": int(reconciled["is_exception"].sum()),
        "exception_rate_pct": float(100 * reconciled["is_exception"].mean()),
        "simulation_window_days": n_days,
        "avg_daily_leakage_kes": float(total_leakage / n_days),
        "annualized_leakage_kes": float(total_leakage / n_days * 365),
    }
