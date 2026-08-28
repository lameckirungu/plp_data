from __future__ import annotations

from pathlib import Path

import pandas as pd

from pumpguard.model import score_latest_assets, train_model

ROOT = Path(__file__).resolve().parents[1]


def test_training_and_scoring_are_complete():
    history = pd.read_csv(ROOT / "data/training_history.csv", parse_dates=["timestamp"])
    demo = pd.read_csv(ROOT / "data/demo_telemetry.csv", parse_dates=["timestamp"])
    bundle = train_model(history, seed=42, cv_folds=3)
    scored = score_latest_assets(bundle, demo)

    assert len(scored) == demo.asset_id.nunique() == 24
    assert scored.risk_probability.between(0, 1).all()
    assert set(scored.risk_band).issubset({"Critical", "Watch", "Normal"})
    assert scored.recommended_action.notna().all()
    assert scored.top_risk_drivers.str.len().gt(0).all()
    assert 0.05 <= bundle.threshold <= 0.95


def test_training_is_deterministic():
    history = pd.read_csv(ROOT / "data/training_history.csv", parse_dates=["timestamp"])
    first = train_model(history, seed=42, cv_folds=3)
    second = train_model(history, seed=42, cv_folds=3)
    assert first.threshold == second.threshold
    assert first.metrics == second.metrics
