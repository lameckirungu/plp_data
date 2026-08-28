"""Create leakage-safe Week 10 training and demo CSVs from Week 6 synthetic data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "week6/data/pdm_synthetic_features.csv"
DESTINATION = Path(__file__).resolve().parents[1] / "data"

RAW = [
    "timestamp",
    "asset_id",
    "depot",
    "shift",
    "asset_age_months",
    "vibration_g",
    "temperature_c",
    "pressure_psi",
    "acoustic_db",
    "motor_current_a",
    "error_events",
]
TARGET = "failure_within_7_days"


def main() -> None:
    source = pd.read_csv(SOURCE)
    source["timestamp"] = pd.to_datetime(source["timestamp"], dayfirst=True)
    source = source.sort_values(["asset_id", "timestamp"])
    # Choose different operating-life points across the fleet so the demo
    # contains a useful mix of routine and elevated-risk pumps instead of 24
    # assets all at the end of their synthetic degradation curves.
    demo_parts = []
    for asset_number, (_, asset_rows) in enumerate(source.groupby("asset_id")):
        endpoint = 12 + (asset_number * 4) % 90
        demo_parts.append(asset_rows.iloc[endpoint - 5 : endpoint + 1])
    demo_source = pd.concat(demo_parts)
    demo = demo_source[RAW].copy()
    training = source.drop(index=demo_source.index)[RAW + [TARGET]].copy()
    # The Week 6 lab intentionally contains a small number of missing sensor
    # readings. Keep them in training for the model's median imputer, but make
    # the bundled operational demo conform to the same strict upload contract
    # users receive. Fill from that pump's recent median, then the fleet median.
    numeric = [column for column in RAW if column not in {"timestamp", "asset_id", "depot", "shift"}]
    for column in numeric:
        demo[column] = demo[column].fillna(demo.groupby("asset_id")[column].transform("median"))
        demo[column] = demo[column].fillna(source[column].median())
    for frame in (training, demo):
        frame["timestamp"] = frame["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

    DESTINATION.mkdir(parents=True, exist_ok=True)
    training.to_csv(DESTINATION / "training_history.csv", index=False)
    demo.to_csv(DESTINATION / "demo_telemetry.csv", index=False)
    print(f"Wrote {len(training):,} training rows and {len(demo):,} demo rows.")


if __name__ == "__main__":
    main()
