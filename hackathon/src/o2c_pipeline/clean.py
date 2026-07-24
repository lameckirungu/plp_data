"""Cleaning layer: turn raw string exports into typed, analysis-ready frames.

Every cleaning function returns `(clean_df, issues)` where `issues` is a
list of dicts describing what was wrong and how many rows it affected --
these accumulate into the data-quality issue log (data/processed/data_quality_issues.csv)
so cleaning decisions are auditable rather than silent.
"""

import pandas as pd

from o2c_pipeline.config import DEFAULT_UNIT_PRICE_KES, DEPOT_ALIASES


def _issue(table: str, check: str, severity: str, count: int, detail: str = "") -> dict:
    return {"table": table, "check": check, "severity": severity, "count": int(count), "detail": detail}


def parse_mixed_datetime(series: pd.Series) -> pd.Series:
    """Parse a column mixing '%Y-%m-%d %H:%M' and '%d/%m/%Y %H:%M' formats.

    The two formats are distinguished unambiguously by separator ('-' vs
    '/'), so each row is routed to the correct explicit format string
    rather than handed to pandas' generic inference -- which would guess a
    single dayfirst convention for the whole column and silently swap day
    and month on every row in the other format.
    """
    series = series.astype("string")
    is_slash = series.str.contains("/", na=False)
    out = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    if is_slash.any():
        out.loc[is_slash] = pd.to_datetime(
            series[is_slash], format="%d/%m/%Y %H:%M", errors="coerce"
        )
    if (~is_slash).any():
        out.loc[~is_slash] = pd.to_datetime(
            series[~is_slash], format="%Y-%m-%d %H:%M", errors="coerce"
        )
    return out


def parse_amount(series: pd.Series) -> pd.Series:
    """Numeric-ise a column that may contain comma-thousands formatting."""
    cleaned = series.astype("string").str.replace(",", "", regex=False).str.strip()
    return pd.to_numeric(cleaned, errors="coerce").astype(float)


def parse_numeric(series: pd.Series) -> pd.Series:
    """pd.to_numeric infers int64 when a column has no NaNs, which then
    fails schemas that require float64. Force float so dtype is stable
    regardless of whether any given batch happens to contain a null."""
    return pd.to_numeric(series, errors="coerce").astype(float)


def normalize_depot(series: pd.Series) -> pd.Series:
    key = series.astype("string").str.strip().str.lower()
    return key.map(DEPOT_ALIASES).astype("string")


def clean_loading_events(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    issues = []
    df = raw.copy()

    df["depot"] = normalize_depot(df["depot"])
    unmapped = df["depot"].isna().sum()
    if unmapped:
        issues.append(_issue("loading_events", "unmapped_depot_alias", "warning", unmapped))

    for col in ("volume_loaded_litres", "meter_start", "meter_end"):
        df[col] = parse_numeric(df[col])

    df["loading_ts"] = parse_mixed_datetime(df["loading_ts"])
    bad_dates = df["loading_ts"].isna().sum()
    if bad_dates:
        issues.append(_issue("loading_events", "unparseable_loading_ts", "critical", bad_dates))

    missing_customer = df["customer"].isna().sum()
    if missing_customer:
        issues.append(_issue("loading_events", "missing_customer", "warning", missing_customer))
        df["customer"] = df["customer"].fillna("UNKNOWN CUSTOMER")

    # Meter delta vs. declared volume is a cross-check, not a hard failure --
    # large gaps get surfaced downstream as a metering-integrity signal.
    df["meter_delta_litres"] = df["meter_end"] - df["meter_start"]

    dupes = df["loading_id"].duplicated().sum()
    if dupes:
        issues.append(_issue("loading_events", "duplicate_loading_id", "critical", dupes))
        df = df.drop_duplicates(subset="loading_id", keep="first")

    bad_volume = (df["volume_loaded_litres"] <= 0) | df["volume_loaded_litres"].isna()
    if bad_volume.any():
        issues.append(_issue("loading_events", "non_positive_volume", "critical", bad_volume.sum()))
        df = df[~bad_volume]

    return df.reset_index(drop=True), issues


def clean_dispatch_events(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    issues = []
    df = raw.copy()

    df["volume_dispatched_litres"] = parse_numeric(df["volume_dispatched_litres"])
    df["dispatch_ts"] = parse_mixed_datetime(df["dispatch_ts"])
    bad_dates = df["dispatch_ts"].isna().sum()
    if bad_dates:
        issues.append(_issue("dispatch_events", "unparseable_dispatch_ts", "critical", bad_dates))

    dupes = df["dispatch_id"].duplicated().sum()
    if dupes:
        issues.append(_issue("dispatch_events", "duplicate_dispatch_id", "critical", dupes))
        df = df.drop_duplicates(subset="dispatch_id", keep="first")

    bad_volume = (df["volume_dispatched_litres"] <= 0) | df["volume_dispatched_litres"].isna()
    if bad_volume.any():
        issues.append(_issue("dispatch_events", "non_positive_volume", "critical", bad_volume.sum()))
        df = df[~bad_volume]

    return df.reset_index(drop=True), issues


def clean_invoices(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    issues = []
    df = raw.copy()

    df["volume_invoiced_litres"] = parse_numeric(df["volume_invoiced_litres"])
    df["amount_kes"] = parse_amount(df["amount_kes"])
    df["unit_price_kes"] = parse_amount(df["unit_price_kes"])
    df["invoice_date"] = parse_mixed_datetime(df["invoice_date"])

    bad_dates = df["invoice_date"].isna().sum()
    if bad_dates:
        issues.append(_issue("invoices", "unparseable_invoice_date", "critical", bad_dates))

    # Backfill a missing unit price from amount / volume where possible,
    # otherwise fall back to the product's default ex-depot price so
    # reconciliation always has a valuation to work with.
    missing_price = df["unit_price_kes"].isna()
    if missing_price.any():
        issues.append(_issue("invoices", "missing_unit_price_backfilled", "warning", missing_price.sum()))
        derivable = missing_price & df["amount_kes"].notna() & (df["volume_invoiced_litres"] > 0)
        df.loc[derivable, "unit_price_kes"] = (
            df.loc[derivable, "amount_kes"] / df.loc[derivable, "volume_invoiced_litres"]
        )
        still_missing = df["unit_price_kes"].isna()
        df.loc[still_missing, "unit_price_kes"] = df.loc[still_missing, "product"].map(
            DEFAULT_UNIT_PRICE_KES
        )

    missing_amount = df["amount_kes"].isna()
    if missing_amount.any():
        issues.append(_issue("invoices", "missing_amount_backfilled", "warning", missing_amount.sum()))
        df.loc[missing_amount, "amount_kes"] = (
            df.loc[missing_amount, "volume_invoiced_litres"] * df.loc[missing_amount, "unit_price_kes"]
        )

    dupes = df["invoice_id"].duplicated().sum()
    if dupes:
        issues.append(_issue("invoices", "duplicate_invoice_id", "critical", dupes))
        df = df.drop_duplicates(subset="invoice_id", keep="first")

    # An invoice_id is a unique document, but the SAME dispatch_id being
    # billed on more than one invoice document is a real audit exception
    # (double billing risk) -- flagged here, resolved in reconciliation.
    dispatch_multi_invoice = df["dispatch_id"].duplicated(keep=False).sum()
    if dispatch_multi_invoice:
        issues.append(
            _issue(
                "invoices", "dispatch_with_multiple_invoices", "exception", dispatch_multi_invoice
            )
        )

    return df.reset_index(drop=True), issues


def clean_payments(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    issues = []
    df = raw.copy()

    df["amount_paid_kes"] = parse_amount(df["amount_paid_kes"])
    df["payment_date"] = parse_mixed_datetime(df["payment_date"])

    bad_dates = df["payment_date"].isna().sum()
    if bad_dates:
        issues.append(_issue("payments", "unparseable_payment_date", "critical", bad_dates))

    dupes = df["payment_id"].duplicated().sum()
    if dupes:
        issues.append(_issue("payments", "duplicate_payment_id", "critical", dupes))
        df = df.drop_duplicates(subset="payment_id", keep="first")

    bad_amount = (df["amount_paid_kes"] <= 0) | df["amount_paid_kes"].isna()
    if bad_amount.any():
        issues.append(_issue("payments", "non_positive_amount", "critical", bad_amount.sum()))
        df = df[~bad_amount]

    return df.reset_index(drop=True), issues


def clean_all(raw: dict) -> tuple[dict, pd.DataFrame]:
    """Clean every raw table and return (cleaned_tables, issues_log)."""
    all_issues = []

    loadings, issues = clean_loading_events(raw["loading_events"])
    all_issues += issues

    dispatches, issues = clean_dispatch_events(raw["dispatch_events"])
    all_issues += issues

    invoices, issues = clean_invoices(raw["invoices"])
    all_issues += issues

    payments, issues = clean_payments(raw["payments"])
    all_issues += issues

    cleaned = {
        "loading_events": loadings,
        "dispatch_events": dispatches,
        "invoices": invoices,
        "payments": payments,
    }
    issues_df = pd.DataFrame(
        all_issues, columns=["table", "check", "severity", "count", "detail"]
    )
    return cleaned, issues_df
