from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
def telemetry() -> pd.DataFrame:
    rows = []
    for asset_number, depot in [(1, "North"), (2, "South")]:
        for reading in range(6):
            rows.append(
                {
                    "timestamp": f"2026-01-{reading + 1:02d} 00:00:00",
                    "asset_id": f"PUMP-{asset_number:03d}",
                    "depot": depot,
                    "shift": "Day" if reading % 2 == 0 else "Night",
                    "asset_age_months": 20 + asset_number,
                    "vibration_g": 1.0 + reading * 0.2 + asset_number * 0.1,
                    "temperature_c": 60 + reading + asset_number,
                    "pressure_psi": 120 - reading,
                    "acoustic_db": 70 + reading * 0.3,
                    "motor_current_a": 35 + reading * 0.4,
                    "error_events": reading % 3,
                }
            )
    return pd.DataFrame(rows)
