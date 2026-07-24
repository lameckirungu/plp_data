"""Shared paths and domain constants for the order-to-cash pipeline."""

import os
from pathlib import Path

# Resolved from the working directory (overridable via O2C_ROOT_DIR), not
# from this file's own location -- `__file__`-relative parents only work
# for an editable, src-layout checkout. Once the package is `pip install`ed
# normally (e.g. the Docker image), this file lives under site-packages and
# a parents[] walk from there points at the wrong place entirely. Every
# entry point (pipeline, dashboard, tests, scripts) is run with the repo
# root as cwd, so that is the correct default.
ROOT_DIR = Path(os.environ.get("O2C_ROOT_DIR", Path.cwd()))
DATA_RAW_DIR = ROOT_DIR / "data" / "raw"
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "processed"
REPORTS_DIR = ROOT_DIR / "reports"

LOADING_EVENTS_RAW = DATA_RAW_DIR / "loading_events.csv"
DISPATCH_EVENTS_RAW = DATA_RAW_DIR / "dispatch_events.csv"
INVOICES_RAW = DATA_RAW_DIR / "invoices.csv"
PAYMENTS_RAW = DATA_RAW_DIR / "payments.csv"

RECONCILED_OUTPUT = DATA_PROCESSED_DIR / "reconciled_order_to_cash.csv"
LEAKAGE_SUMMARY_JSON = REPORTS_DIR / "leakage_summary.json"
LEAKAGE_CHART_PNG = REPORTS_DIR / "leakage_analysis.png"
DQ_ISSUES_LOG = DATA_PROCESSED_DIR / "data_quality_issues.csv"

# Canonical depot names. Raw exports contain casing/abbreviation drift that
# clean.py normalizes against this list.
DEPOTS = ["Mombasa", "Nairobi", "Kisumu", "Eldoret", "Nakuru", "Kisii"]

DEPOT_ALIASES = {
    "mombasa": "Mombasa",
    "msa": "Mombasa",
    "nairobi": "Nairobi",
    "nrb": "Nairobi",
    "nairobi depot": "Nairobi",
    "kisumu": "Kisumu",
    "ksm": "Kisumu",
    "eldoret": "Eldoret",
    "eld": "Eldoret",
    "nakuru": "Nakuru",
    "nku": "Nakuru",
    "kisii": "Kisii",
}

# Product codes as used on KPC billing documents, mapped to display names.
PRODUCTS = {
    "PMS": "Premium Motor Spirit (Petrol)",
    "AGO": "Automotive Gas Oil (Diesel)",
    "IK": "Illuminating Kerosene",
}

# Approximate ex-depot unit price in KES per litre, used to value volumes
# that are missing a price on the raw invoice.
DEFAULT_UNIT_PRICE_KES = {
    "PMS": 165.50,
    "AGO": 155.20,
    "IK": 140.00,
}

# Tolerance bands used by the reconciliation and data-quality logic.
VOLUME_VARIANCE_TOLERANCE_PCT = 0.5  # normal metering/temperature variance
SHRINKAGE_ALERT_THRESHOLD_PCT = 2.0  # beyond this, flag as material loss
MAX_INVOICE_LAG_DAYS = 5
MAX_PAYMENT_LAG_DAYS = 30
