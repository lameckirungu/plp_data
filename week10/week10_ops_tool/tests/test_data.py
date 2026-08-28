from __future__ import annotations

import pandas as pd
import pytest

from pumpguard.data import TelemetryValidationError, validate_telemetry


def test_valid_telemetry_is_sorted_and_normalized(telemetry):
    result = validate_telemetry(telemetry.sample(frac=1, random_state=2))
    assert len(result.data) == 12
    assert pd.api.types.is_datetime64_any_dtype(result.data.timestamp)
    assert result.data.iloc[0].asset_id == "PUMP-001"


def test_outcome_columns_are_ignored_with_warning(telemetry):
    telemetry["failure_within_7_days"] = 1
    result = validate_telemetry(telemetry)
    assert "failure_within_7_days" not in result.data
    assert "Outcome fields were ignored" in result.warnings[0]


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (lambda frame: frame.drop(columns="vibration_g"), "Missing required columns"),
        (lambda frame: frame.assign(timestamp="not-a-date"), "invalid timestamp"),
        (lambda frame: frame.assign(temperature_c="hot"), "nonnumeric temperature_c"),
        (lambda frame: pd.concat([frame, frame.iloc[[0]]]), "duplicate asset_id/timestamp"),
        (lambda frame: frame.assign(shift="Swing"), "shift must be Day or Night"),
        (lambda frame: frame.assign(vibration_g=-1), "negative vibration_g"),
    ],
)
def test_invalid_inputs_fail_with_actionable_message(telemetry, mutate, expected):
    with pytest.raises(TelemetryValidationError, match=expected):
        validate_telemetry(mutate(telemetry.copy()))
