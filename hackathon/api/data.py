"""Data access helpers for the API layer.

Reads are done fresh from disk per request rather than cached in memory:
the reconciled dataset is ~2,800 rows (well under 100ms to parse), the
data only changes when someone explicitly triggers a pipeline re-run, and
a stale in-memory cache after a re-run is a worse bug than a few extra
milliseconds per request.
"""

import json

import pandas as pd

from o2c_pipeline.config import (
    DQ_ISSUES_LOG,
    LEAKAGE_SUMMARY_JSON,
    RECONCILED_OUTPUT,
)
from o2c_pipeline.pipeline import PIPELINE_RUN_LOG


def load_summary() -> dict:
    if not LEAKAGE_SUMMARY_JSON.exists():
        raise FileNotFoundError("No pipeline output yet -- POST /api/pipeline/run first")
    with open(LEAKAGE_SUMMARY_JSON) as f:
        return json.load(f)


def load_reconciled() -> pd.DataFrame:
    if not RECONCILED_OUTPUT.exists():
        raise FileNotFoundError("No pipeline output yet -- POST /api/pipeline/run first")
    return pd.read_csv(
        RECONCILED_OUTPUT,
        parse_dates=["loading_ts", "dispatch_ts", "invoice_date"],
    )


def load_dq_issues() -> pd.DataFrame:
    if not DQ_ISSUES_LOG.exists():
        return pd.DataFrame(columns=["table", "check", "severity", "count", "detail"])
    # An empty `detail` cell round-trips through CSV as NaN, which is not
    # valid JSON (float('nan') fails strict json.dumps) -- normalize back
    # to "" so every downstream consumer of this table can serialize it.
    df = pd.read_csv(DQ_ISSUES_LOG)
    df["detail"] = df["detail"].fillna("")
    return df


def load_run_log() -> dict:
    if not PIPELINE_RUN_LOG.exists():
        return {}
    with open(PIPELINE_RUN_LOG) as f:
        return json.load(f)


def apply_filters(
    df: pd.DataFrame,
    depot: list[str] | None = None,
    product: list[str] | None = None,
    customer: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    exceptions_only: bool = False,
) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    if depot:
        mask &= df["depot"].isin(depot)
    if product:
        mask &= df["product"].isin(product)
    if customer:
        mask &= df["customer"].str.contains(customer, case=False, na=False)
    if start_date:
        mask &= df["loading_ts"].dt.date >= pd.Timestamp(start_date).date()
    if end_date:
        mask &= df["loading_ts"].dt.date <= pd.Timestamp(end_date).date()
    if exceptions_only:
        mask &= df["is_exception"]
    return df[mask]
