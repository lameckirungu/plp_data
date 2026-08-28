"""Leakage-safe feature engineering shared by training and inference."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .data import REQUIRED_COLUMNS

ROLLING_COLUMNS = [
    "vibration_roll_mean_6",
    "vibration_rms_6",
    "vibration_peak_to_peak_6",
    "temp_roll_mean_6",
]
NUMERIC_FEATURES = [
    "asset_age_months",
    "vibration_g",
    "temperature_c",
    "pressure_psi",
    "acoustic_db",
    "motor_current_a",
    "error_events",
] + ROLLING_COLUMNS
CATEGORICAL_FEATURES = ["depot", "shift"]
MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def engineer_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Compute six-reading rolling signals independently for each asset."""
    featured = frame.copy().sort_values(["asset_id", "timestamp"])
    grouped_vibration = featured.groupby("asset_id", sort=False)["vibration_g"]
    grouped_temperature = featured.groupby("asset_id", sort=False)["temperature_c"]

    featured["vibration_roll_mean_6"] = grouped_vibration.transform(
        lambda values: values.rolling(6, min_periods=1).mean()
    )
    featured["vibration_rms_6"] = grouped_vibration.transform(
        lambda values: values.rolling(6, min_periods=1).apply(
            lambda window: float(np.sqrt(np.mean(np.square(window)))), raw=True
        )
    )
    featured["vibration_peak_to_peak_6"] = grouped_vibration.transform(
        lambda values: values.rolling(6, min_periods=1).apply(
            lambda window: float(np.ptp(window)), raw=True
        )
    )
    featured["temp_roll_mean_6"] = grouped_temperature.transform(
        lambda values: values.rolling(6, min_periods=1).mean()
    )
    return featured


def raw_training_columns() -> list[str]:
    """Columns allowed into feature engineering, excluding all outcome proxies."""
    return REQUIRED_COLUMNS.copy()
