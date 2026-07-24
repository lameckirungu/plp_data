"""Raw ingestion: read the four source exports as-is, no interpretation.

Everything is read as string dtype. Type coercion, date parsing, and
normalization are the cleaning layer's job (clean.py) -- ingestion's only
responsibility is getting bytes off disk into a DataFrame without pandas'
automatic dtype inference silently mangling IDs, leading zeros, or mixed
date formats before we get a chance to handle them deliberately.
"""

import pandas as pd

from o2c_pipeline.config import (
    DISPATCH_EVENTS_RAW,
    INVOICES_RAW,
    LOADING_EVENTS_RAW,
    PAYMENTS_RAW,
)


def _read_raw(path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Raw source file not found: {path}. "
            "Run `python scripts/generate_synthetic_data.py` first."
        )
    return pd.read_csv(path, dtype=str, keep_default_na=True, na_values=["", "NA", "N/A", "null"])


def read_loading_events() -> pd.DataFrame:
    return _read_raw(LOADING_EVENTS_RAW)


def read_dispatch_events() -> pd.DataFrame:
    return _read_raw(DISPATCH_EVENTS_RAW)


def read_invoices() -> pd.DataFrame:
    return _read_raw(INVOICES_RAW)


def read_payments() -> pd.DataFrame:
    return _read_raw(PAYMENTS_RAW)


def read_all() -> dict:
    return {
        "loading_events": read_loading_events(),
        "dispatch_events": read_dispatch_events(),
        "invoices": read_invoices(),
        "payments": read_payments(),
    }
