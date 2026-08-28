"""Telemetry loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

IDENTITY_COLUMNS = ["timestamp", "asset_id", "depot", "shift"]
SENSOR_COLUMNS = [
    "asset_age_months",
    "vibration_g",
    "temperature_c",
    "pressure_psi",
    "acoustic_db",
    "motor_current_a",
    "error_events",
]
REQUIRED_COLUMNS = IDENTITY_COLUMNS + SENSOR_COLUMNS
OUTCOME_COLUMNS = {
    "failure_within_7_days",
    "time_to_failure_hours",
    "health_status",
    "fault_type",
}


class TelemetryValidationError(ValueError):
    """Raised when uploaded telemetry cannot be safely scored."""

    def __init__(self, messages: list[str]):
        self.messages = messages
        super().__init__("; ".join(messages))


@dataclass(frozen=True)
class ValidationResult:
    data: pd.DataFrame
    warnings: tuple[str, ...] = ()


def load_csv(path_or_buffer: str | Path | object) -> pd.DataFrame:
    """Load a telemetry CSV without silently changing source values."""
    try:
        return pd.read_csv(path_or_buffer)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise TelemetryValidationError([f"The file is not a readable CSV: {exc}"]) from exc


def validate_telemetry(frame: pd.DataFrame) -> ValidationResult:
    """Validate and normalize telemetry before feature engineering."""
    errors: list[str] = []
    warnings: list[str] = []
    missing_columns = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing_columns:
        errors.append("Missing required columns: " + ", ".join(missing_columns))
        raise TelemetryValidationError(errors)

    if frame.empty:
        raise TelemetryValidationError(["The CSV contains headers but no telemetry rows."])

    present_outcomes = sorted(OUTCOME_COLUMNS.intersection(frame.columns))
    if present_outcomes:
        warnings.append(
            "Outcome fields were ignored during scoring: " + ", ".join(present_outcomes)
        )

    clean = frame[REQUIRED_COLUMNS].copy()
    clean["timestamp"] = pd.to_datetime(
        clean["timestamp"], errors="coerce", format="mixed", dayfirst=True
    )
    bad_dates = int(clean["timestamp"].isna().sum())
    if bad_dates:
        errors.append(f"{bad_dates} row(s) contain an invalid timestamp.")

    for column in SENSOR_COLUMNS:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")
        invalid = int(clean[column].isna().sum())
        if invalid:
            errors.append(f"{invalid} row(s) contain a missing or nonnumeric {column} value.")
        negative = int((clean[column] < 0).sum())
        if negative:
            errors.append(f"{negative} row(s) contain a negative {column} value.")

    for column in ["asset_id", "depot", "shift"]:
        clean[column] = clean[column].astype("string").str.strip()
        blank = int((clean[column].isna() | clean[column].eq("")).sum())
        if blank:
            errors.append(f"{blank} row(s) contain a blank {column} value.")

    invalid_shifts = sorted(set(clean["shift"].dropna()) - {"Day", "Night"})
    if invalid_shifts:
        errors.append("shift must be Day or Night; found: " + ", ".join(invalid_shifts))

    duplicate_count = int(clean.duplicated(["asset_id", "timestamp"]).sum())
    if duplicate_count:
        errors.append(
            f"{duplicate_count} duplicate asset_id/timestamp row(s) must be resolved."
        )

    if errors:
        raise TelemetryValidationError(errors)

    clean = clean.sort_values(["asset_id", "timestamp"]).reset_index(drop=True)
    if clean.groupby("asset_id").size().min() < 6:
        warnings.append(
            "Some assets have fewer than six readings; rolling features use the available history."
        )
    return ValidationResult(clean, tuple(warnings))
