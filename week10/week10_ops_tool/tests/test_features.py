from __future__ import annotations

import numpy as np

from pumpguard.features import MODEL_FEATURES, engineer_features, raw_training_columns


def test_rolling_features_are_asset_isolated(telemetry):
    featured = engineer_features(telemetry)
    pump_one = featured[featured.asset_id == "PUMP-001"]
    assert pump_one.iloc[0].vibration_roll_mean_6 == pump_one.iloc[0].vibration_g
    expected_rms = np.sqrt(np.mean(np.square(pump_one.vibration_g)))
    assert np.isclose(pump_one.iloc[-1].vibration_rms_6, expected_rms)


def test_outcome_proxies_never_enter_model_features():
    forbidden = {"failure_within_7_days", "time_to_failure_hours", "health_status", "fault_type"}
    assert forbidden.isdisjoint(MODEL_FEATURES)
    assert forbidden.isdisjoint(raw_training_columns())
