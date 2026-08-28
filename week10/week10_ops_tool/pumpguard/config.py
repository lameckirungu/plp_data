"""Environment-backed settings for PumpGuard Ops."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    app_title: str = os.getenv("PUMPGUARD_APP_TITLE", "PumpGuard Ops")
    random_seed: int = int(os.getenv("PUMPGUARD_RANDOM_SEED", "42"))
    cv_folds: int = int(os.getenv("PUMPGUARD_CV_FOLDS", "5"))
    training_data: Path = ROOT / os.getenv(
        "PUMPGUARD_TRAINING_DATA", "data/training_history.csv"
    )
    demo_data: Path = ROOT / os.getenv(
        "PUMPGUARD_DEMO_DATA", "data/demo_telemetry.csv"
    )


SETTINGS = Settings()
