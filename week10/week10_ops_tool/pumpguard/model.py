"""Model training, threshold policy, scoring, and local explanations."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import xgboost as xgb
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

from .features import (
    CATEGORICAL_FEATURES,
    MODEL_FEATURES,
    NUMERIC_FEATURES,
    engineer_features,
)

TARGET = "failure_within_7_days"


@dataclass(frozen=True)
class ModelBundle:
    pipeline: ImbPipeline
    threshold: float
    metrics: dict[str, float]
    threshold_note: str
    feature_names: tuple[str, ...]


def build_pipeline(seed: int = 42) -> ImbPipeline:
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    preprocessor = ColumnTransformer(
        [("num", numeric, NUMERIC_FEATURES), ("cat", categorical, CATEGORICAL_FEATURES)]
    )
    classifier = XGBClassifier(
        n_estimators=250,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.9,
        eval_metric="logloss",
        random_state=seed,
        n_jobs=1,
    )
    return ImbPipeline(
        [
            ("preprocessor", preprocessor),
            ("smote", SMOTE(random_state=seed, k_neighbors=5)),
            ("model", classifier),
        ]
    )


def _threshold_table(y_true: pd.Series, probability: np.ndarray) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    for threshold in np.arange(0.05, 0.951, 0.01):
        prediction = (probability >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, prediction, labels=[0, 1]).ravel()
        rows.append(
            {
                "threshold": float(threshold),
                "precision": precision_score(y_true, prediction, zero_division=0),
                "recall": recall_score(y_true, prediction, zero_division=0),
                "f1": f1_score(y_true, prediction, zero_division=0),
                "false_positive_rate": fp / (fp + tn) if fp + tn else 0.0,
            }
        )
    return pd.DataFrame(rows)


def _select_threshold(table: pd.DataFrame) -> tuple[pd.Series, str]:
    feasible = table[(table.recall >= 0.80) & (table.false_positive_rate <= 0.05)]
    if not feasible.empty:
        selected = feasible.sort_values(["f1", "recall"], ascending=False).iloc[0]
        return selected, "Operational targets met: recall ≥80% and false-positive rate ≤5%."

    fpr_constrained = table[table.false_positive_rate <= 0.05]
    if not fpr_constrained.empty:
        selected = fpr_constrained.sort_values(["recall", "f1"], ascending=False).iloc[0]
        return selected, (
            "No threshold met both targets; selected the highest-recall point with "
            "false-positive rate ≤5%."
        )

    selected = table.sort_values("f1", ascending=False).iloc[0]
    return selected, "No point met the false-positive constraint; selected maximum F1."


def train_model(history: pd.DataFrame, seed: int = 42, cv_folds: int = 5) -> ModelBundle:
    """Train with grouped out-of-fold threshold evaluation, then refit all history."""
    required = {TARGET, "asset_id"}
    missing = required - set(history.columns)
    if missing:
        raise ValueError("Training data missing: " + ", ".join(sorted(missing)))

    featured = engineer_features(history)
    X = featured[MODEL_FEATURES]
    y = featured[TARGET].astype(int)
    groups = featured["asset_id"]
    folds = min(cv_folds, groups.nunique())
    if folds < 2:
        raise ValueError("Training requires at least two distinct assets.")

    pipeline = build_pipeline(seed)
    cv = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=seed)
    probabilities = cross_val_predict(
        pipeline, X, y, groups=groups, cv=cv, method="predict_proba", n_jobs=1
    )[:, 1]
    table = _threshold_table(y, probabilities)
    selected, note = _select_threshold(table)
    threshold = float(selected.threshold)
    prediction = (probabilities >= threshold).astype(int)

    metrics = {
        "roc_auc": float(roc_auc_score(y, probabilities)),
        "precision": float(precision_score(y, prediction, zero_division=0)),
        "recall": float(recall_score(y, prediction, zero_division=0)),
        "f1": float(f1_score(y, prediction, zero_division=0)),
        "false_positive_rate": float(selected.false_positive_rate),
    }
    pipeline.fit(X, y)
    names = tuple(
        pipeline.named_steps["preprocessor"].get_feature_names_out().tolist()
    )
    return ModelBundle(pipeline, threshold, metrics, note, names)


def _friendly_feature_name(name: str) -> str:
    clean = name.split("__", 1)[-1]
    replacements = {
        "vibration_g": "vibration",
        "temperature_c": "temperature",
        "pressure_psi": "pressure",
        "acoustic_db": "acoustic level",
        "motor_current_a": "motor current",
        "error_events": "error events",
        "asset_age_months": "asset age",
        "vibration_roll_mean_6": "rolling vibration",
        "vibration_rms_6": "vibration RMS",
        "vibration_peak_to_peak_6": "vibration range",
        "temp_roll_mean_6": "rolling temperature",
    }
    if clean in replacements:
        return replacements[clean]
    if clean.startswith("depot_"):
        return "depot: " + clean.removeprefix("depot_")
    if clean.startswith("shift_"):
        return "shift: " + clean.removeprefix("shift_")
    return clean.replace("_", " ")


def _risk_band(probability: float, threshold: float) -> str:
    if probability >= threshold:
        return "Critical"
    if probability >= threshold * 0.5:
        return "Watch"
    return "Normal"


def score_latest_assets(bundle: ModelBundle, telemetry: pd.DataFrame) -> pd.DataFrame:
    """Score the latest engineered snapshot for every asset."""
    featured = engineer_features(telemetry)
    latest = (
        featured.sort_values("timestamp").groupby("asset_id", as_index=False).tail(1).copy()
    )
    X = latest[MODEL_FEATURES]
    probabilities = bundle.pipeline.predict_proba(X)[:, 1]

    transformed = bundle.pipeline.named_steps["preprocessor"].transform(X)
    contributions = bundle.pipeline.named_steps["model"].get_booster().predict(
        xgb.DMatrix(transformed), pred_contribs=True
    )[:, :-1]

    explanations: list[str] = []
    for values in contributions:
        positive = [(i, value) for i, value in enumerate(values) if value > 0]
        ranked = sorted(positive, key=lambda item: item[1], reverse=True)[:3]
        if ranked:
            explanations.append(", ".join(_friendly_feature_name(bundle.feature_names[i]) for i, _ in ranked))
        else:
            explanations.append("no positive risk contribution identified")

    result = latest[["asset_id", "depot", "timestamp"]].copy()
    result["risk_probability"] = probabilities
    result["risk_band"] = [
        _risk_band(value, bundle.threshold) for value in probabilities
    ]
    actions = {
        "Critical": "Inspect within 24 hours",
        "Watch": "Review within 7 days",
        "Normal": "Continue routine monitoring",
    }
    result["recommended_action"] = result["risk_band"].map(actions)
    result["top_risk_drivers"] = explanations
    result = result.sort_values("risk_probability", ascending=False).reset_index(drop=True)
    return result
