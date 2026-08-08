from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from scipy import stats
from sklearn.ensemble import BaggingClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
NOTEBOOK_DIR = ROOT / "notebooks"
DELIVERABLE_DIR = ROOT / "deliverables"
FIGURE_DIR = DELIVERABLE_DIR / "figures"


def ensure_dirs() -> None:
    for path in [DATA_DIR, NOTEBOOK_DIR, DELIVERABLE_DIR, FIGURE_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def make_dataset(seed: int = 42, n_assets: int = 24, n_per_asset: int = 110) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    depots = np.array(["North", "South", "East", "West"])
    shifts = np.array(["Day", "Night"])

    for asset_idx in range(n_assets):
        asset_id = f"PUMP-{asset_idx + 1:03d}"
        depot = depots[asset_idx % len(depots)]
        age_months = int(rng.integers(8, 96))
        fault_start = int(rng.integers(62, 92))
        base_vibration = rng.normal(1.8, 0.25)
        base_temp = rng.normal(62, 3)
        base_pressure = rng.normal(118, 7)

        for t in range(n_per_asset):
            degradation = max(0, (t - fault_start) / max(1, n_per_asset - fault_start))
            shift = rng.choice(shifts, p=[0.56, 0.44])
            night_penalty = 0.09 if shift == "Night" else 0
            vibration = base_vibration + 2.8 * degradation + night_penalty + rng.normal(0, 0.18)
            temperature = base_temp + 19 * degradation + 1.2 * night_penalty + rng.normal(0, 1.8)
            pressure = base_pressure - 16 * degradation + rng.normal(0, 3.6)
            acoustic_db = 70 + 9 * degradation + rng.normal(0, 2.3)
            motor_current = 36 + 7.5 * degradation + rng.normal(0, 1.4)
            error_events = rng.poisson(0.18 + 1.8 * degradation + (0.18 if shift == "Night" else 0))
            time_to_failure = max(0, n_per_asset - t - rng.normal(0, 4))

            if degradation >= 0.72:
                fault_type = rng.choice(["Bearing Wear", "Seal Leak", "Misalignment"], p=[0.58, 0.27, 0.15])
            elif degradation >= 0.35:
                fault_type = rng.choice(["Warning", "Bearing Wear", "Seal Leak"], p=[0.74, 0.18, 0.08])
            else:
                fault_type = "Normal"

            health_status = "Healthy"
            if vibration > 3.0 or temperature > 76 or error_events >= 2:
                health_status = "Warning"
            if vibration > 4.1 or temperature > 85 or pressure < 98 or error_events >= 4:
                health_status = "Critical"

            rows.append(
                {
                    "timestamp": pd.Timestamp("2026-01-01") + pd.Timedelta(hours=6 * t),
                    "asset_id": asset_id,
                    "depot": depot,
                    "shift": shift,
                    "asset_age_months": age_months,
                    "vibration_g": round(vibration, 4),
                    "temperature_c": round(temperature, 4),
                    "pressure_psi": round(pressure, 4),
                    "acoustic_db": round(acoustic_db, 4),
                    "motor_current_a": round(motor_current, 4),
                    "error_events": int(error_events),
                    "constant_sensor": 1.0,
                    "time_to_failure_hours": round(time_to_failure * 6, 2),
                    "health_status": health_status,
                    "fault_type": fault_type,
                    "failure_within_7_days": int(time_to_failure <= 28 or health_status == "Critical"),
                }
            )

    df = pd.DataFrame(rows)

    outlier_indices = rng.choice(df.index, size=12, replace=False)
    df.loc[outlier_indices[:6], "vibration_g"] *= 3.8
    df.loc[outlier_indices[6:], "temperature_c"] += 55
    missing_indices = rng.choice(df.index, size=18, replace=False)
    df.loc[missing_indices[:9], "pressure_psi"] = np.nan
    df.loc[missing_indices[9:], "acoustic_db"] = np.nan
    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.sort_values(["asset_id", "timestamp"]).copy()
    out["vibration_roll_mean_6"] = (
        out.groupby("asset_id")["vibration_g"].transform(lambda s: s.rolling(6, min_periods=1).mean())
    )
    out["vibration_rms_6"] = out.groupby("asset_id")["vibration_g"].transform(
        lambda s: np.sqrt(s.pow(2).rolling(6, min_periods=1).mean())
    )
    out["vibration_peak_to_peak_6"] = out.groupby("asset_id")["vibration_g"].transform(
        lambda s: s.rolling(6, min_periods=1).max() - s.rolling(6, min_periods=1).min()
    )
    out["temp_roll_mean_6"] = (
        out.groupby("asset_id")["temperature_c"].transform(lambda s: s.rolling(6, min_periods=1).mean())
    )
    return out


def write_notebook() -> None:
    cells = [
        md("# Statistical Foundations & Predictive Maintenance Lab\nThis notebook performs cleaning, hypothesis testing, feature engineering, modeling, and RUL estimation on the synthetic PdM dataset."),
        code("import pandas as pd\nimport numpy as np\nfrom scipy import stats\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.ensemble import BaggingClassifier\nfrom sklearn.tree import DecisionTreeClassifier\nfrom sklearn.metrics import confusion_matrix, classification_report, mean_absolute_error\nfrom sklearn.linear_model import LinearRegression\n\nDATA_PATH = '../data/pdm_synthetic_sensor_data.csv'\ndf = pd.read_csv(DATA_PATH, parse_dates=['timestamp'])\ndf.shape, df.head()"),
        code("# Descriptive statistics and cleaning checks\nnumeric = df.select_dtypes(include='number')\nsummary = numeric.describe(percentiles=[.05, .25, .5, .75, .95]).T\nconstant_columns = [c for c in df.columns if df[c].nunique(dropna=False) == 1]\nmissing_counts = df.isna().sum().sort_values(ascending=False)\nsummary.head(), constant_columns, missing_counts.head()"),
        code("# Three-standard-deviation outlier flags\nz = (numeric - numeric.mean()) / numeric.std(ddof=0)\noutlier_counts = (z.abs() > 3).sum().sort_values(ascending=False)\noutlier_counts.head(10)"),
        code("# Independent t-test: Day vs Night vibration levels\nday = df.loc[df['shift'] == 'Day', 'vibration_g'].dropna()\nnight = df.loc[df['shift'] == 'Night', 'vibration_g'].dropna()\nt_stat, p_value = stats.ttest_ind(day, night, equal_var=False)\nprint({'t_statistic': round(t_stat, 4), 'p_value': round(p_value, 6), 'day_mean': day.mean(), 'night_mean': night.mean()})\nprint('Reject H0: shift means differ' if p_value < 0.05 else 'Fail to reject H0')"),
        code("# ANOVA: throughput proxy across depots using pressure\nsamples = [g['pressure_psi'].dropna() for _, g in df.groupby('depot')]\nf_stat, anova_p = stats.f_oneway(*samples)\nprint({'f_statistic': round(f_stat, 4), 'p_value': round(anova_p, 6)})"),
        code("# Feature engineering: rolling mean, RMS, and peak-to-peak\nwork = df.sort_values(['asset_id', 'timestamp']).copy()\nwork['vibration_roll_mean_6'] = work.groupby('asset_id')['vibration_g'].transform(lambda s: s.rolling(6, min_periods=1).mean())\nwork['vibration_rms_6'] = work.groupby('asset_id')['vibration_g'].transform(lambda s: np.sqrt(s.pow(2).rolling(6, min_periods=1).mean()))\nwork['vibration_peak_to_peak_6'] = work.groupby('asset_id')['vibration_g'].transform(lambda s: s.rolling(6, min_periods=1).max() - s.rolling(6, min_periods=1).min())\nwork[['asset_id','timestamp','vibration_g','vibration_roll_mean_6','vibration_rms_6','vibration_peak_to_peak_6']].head(10)"),
        code("# Bagged tree classifier: predict failure within 7 days\nfeatures = ['asset_age_months','vibration_g','temperature_c','pressure_psi','acoustic_db','motor_current_a','error_events','vibration_roll_mean_6','vibration_rms_6','vibration_peak_to_peak_6']\nmodel_df = work[features + ['failure_within_7_days']].dropna()\nX_train, X_test, y_train, y_test = train_test_split(model_df[features], model_df['failure_within_7_days'], test_size=0.25, random_state=42, stratify=model_df['failure_within_7_days'])\nclf = BaggingClassifier(estimator=DecisionTreeClassifier(max_depth=5, random_state=42), n_estimators=40, random_state=42)\nclf.fit(X_train, y_train)\npred = clf.predict(X_test)\nprint(confusion_matrix(y_test, pred))\nprint(classification_report(y_test, pred, target_names=['No near failure','Near failure']))"),
        code("# Remaining Useful Life regression baseline\nreg = LinearRegression()\nrul_df = work[features + ['time_to_failure_hours']].dropna()\nX_train, X_test, y_train, y_test = train_test_split(rul_df[features], rul_df['time_to_failure_hours'], test_size=0.25, random_state=42)\nreg.fit(X_train, y_train)\nrul_pred = reg.predict(X_test)\nprint({'mae_hours': round(mean_absolute_error(y_test, rul_pred), 2)})"),
    ]
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.x"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (NOTEBOOK_DIR / "pdm_lab_notebook.ipynb").write_text(json.dumps(nb, indent=2), encoding="utf-8")


def md(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(True)}


def code(source: str) -> dict:
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.splitlines(True)}


def make_pdf(metrics: dict) -> None:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8.8, leading=11))
    story = []
    doc = SimpleDocTemplate(
        str(DELIVERABLE_DIR / "communication_briefs.pdf"),
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    story.append(Paragraph("Brief A: Technical Maintenance Engineering", styles["Title"]))
    story.append(Paragraph("Objective: detect near-term pump failure from vibration, temperature, pressure, acoustic, current, and event-count data.", styles["Small"]))
    story.append(Spacer(1, 0.12 * inch))
    tech_rows = [
        ["Metric", "Result", "Interpretation"],
        ["Model", "Bagged decision trees", "Robust baseline for non-linear fault patterns."],
        ["Accuracy", f"{metrics['accuracy']:.1%}", "Share with sensitivity and false-alarm rate, not alone."],
        ["Sensitivity", f"{metrics['sensitivity']:.1%}", "Percent of near failures caught before intervention window closes."],
        ["False alarm rate", f"{metrics['false_alarm_rate']:.1%}", "Healthy observations incorrectly escalated for maintenance review."],
        ["Shift t-test p-value", f"{metrics['ttest_p']:.5f}", "Night and day vibration means differ at alpha = 0.05."],
        ["RUL MAE", f"{metrics['rul_mae']:.1f} hours", "Average error for baseline remaining-useful-life prediction."],
    ]
    story.append(table(tech_rows, [1.35 * inch, 1.55 * inch, 4.1 * inch]))
    story.append(Spacer(1, 0.14 * inch))
    story.append(Paragraph("Recommended engineering action: deploy warning thresholds using vibration RMS, temperature trend, and pressure drop logic. Track confusion matrix movement weekly and tune the alert threshold if false alarms exceed operating tolerance.", styles["Small"]))
    story.append(PageBreak())
    story.append(Paragraph("Brief B: CFO / Executive Summary", styles["Title"]))
    story.append(Paragraph("Business issue: unplanned pump failures interrupt throughput, create overtime maintenance work, and increase safety exposure. The predictive maintenance model identifies assets likely to fail within seven days so work can be scheduled before downtime occurs.", styles["Small"]))
    story.append(Spacer(1, 0.12 * inch))
    exec_rows = [
        ["Executive question", "Answer"],
        ["What changes operationally?", "Maintenance shifts from calendar-based work to risk-based scheduling."],
        ["Why fund it?", "The model targets avoided downtime, fewer emergency callouts, and better spare-parts planning."],
        ["Main risk control", f"It catches about {metrics['sensitivity']:.0%} of near failures in the synthetic pilot."],
        ["Cost discipline", "Avoid replacing equipment too early by using condition evidence rather than fixed age alone."],
        ["Success metric", "Reduce avoidable downtime and false alarms while preserving production capacity."],
    ]
    story.append(table(exec_rows, [2.0 * inch, 5.0 * inch]))
    story.append(Spacer(1, 0.14 * inch))
    story.append(Paragraph("Recommended executive action: approve a 90-day pilot on high-criticality pumps, measure avoided downtime, emergency maintenance hours, false alarms, and operator adoption, then decide whether to scale.", styles["Small"]))
    doc.build(story)


def table(rows: list[list[str]], widths: list[float]) -> Table:
    styles = getSampleStyleSheet()
    body = ParagraphStyle(name="CellBody", parent=styles["BodyText"], fontSize=8.5, leading=10.5)
    header = ParagraphStyle(name="CellHeader", parent=body, fontName="Helvetica-Bold", textColor=colors.white)
    wrapped = [
        [Paragraph(cell, header if row_idx == 0 else body) for cell in row]
        for row_idx, row in enumerate(rows)
    ]
    t = Table(wrapped, colWidths=widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("LEADING", (0, 0), (-1, -1), 10.5),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#b7c9d8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f8fb")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return t


def write_proposal(metrics: dict) -> None:
    content = f"""# Capstone Proposal: Predictive Maintenance for Centrifugal Pumps

## Operational Problem Statement
Unplanned pump failures create production losses, emergency labor, and safety risk. The capstone will build a predictive maintenance workflow that identifies pumps likely to fail within seven days and estimates remaining useful life for prioritized maintenance scheduling.

## Source Data
- Synthetic IoT data in `data/pdm_synthetic_sensor_data.csv`
- 2,640 timestamped records across 24 pump assets
- Signals: vibration, temperature, pressure, acoustic level, motor current, error events, shift, depot, health status, fault type, and RUL
- Built-in teaching issues: missing values, outliers, and a constant sensor column with no predictive value

## Analytical Approach
- Clean missing values and flag outliers using the three-standard-deviation rule
- Use an independent t-test to compare day vs. night vibration behavior
- Engineer rolling mean, RMS, and peak-to-peak vibration features
- Train a bagged-tree classifier for seven-day failure risk
- Fit a baseline regression model for remaining useful life

## Success Metrics
- Reduce false alarms by 20% versus a simple threshold rule
- Catch at least 80% of near-failure events during the seven-day intervention window
- Keep RUL mean absolute error below 72 hours in the synthetic benchmark
- Translate model outputs into two stakeholder-ready briefs: one technical, one financial

## Pilot Result Baseline
- Classifier accuracy: {metrics['accuracy']:.1%}
- Sensitivity: {metrics['sensitivity']:.1%}
- False alarm rate: {metrics['false_alarm_rate']:.1%}
- RUL MAE: {metrics['rul_mae']:.1f} hours
"""
    (DELIVERABLE_DIR / "capstone_proposal.md").write_text(content, encoding="utf-8")


def calculate_metrics(df: pd.DataFrame) -> dict:
    work = add_features(df)
    clean = work.dropna()
    features = [
        "asset_age_months",
        "vibration_g",
        "temperature_c",
        "pressure_psi",
        "acoustic_db",
        "motor_current_a",
        "error_events",
        "vibration_roll_mean_6",
        "vibration_rms_6",
        "vibration_peak_to_peak_6",
    ]
    X = clean[features]
    y = clean["failure_within_7_days"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    clf = BaggingClassifier(estimator=DecisionTreeClassifier(max_depth=5, random_state=42), n_estimators=40, random_state=42)
    clf.fit(X_train, y_train)
    pred = clf.predict(X_test)
    tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()

    reg_y = clean["time_to_failure_hours"]
    X_train, X_test, y_train, y_test = train_test_split(X, reg_y, test_size=0.25, random_state=42)
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error

    reg = LinearRegression()
    reg.fit(X_train, y_train)
    rul_mae = mean_absolute_error(y_test, reg.predict(X_test))
    ttest_p = stats.ttest_ind(
        df.loc[df["shift"] == "Day", "vibration_g"].dropna(),
        df.loc[df["shift"] == "Night", "vibration_g"].dropna(),
        equal_var=False,
    ).pvalue
    return {
        "accuracy": (tp + tn) / (tp + tn + fp + fn),
        "sensitivity": tp / (tp + fn),
        "false_alarm_rate": fp / (fp + tn),
        "rul_mae": rul_mae,
        "ttest_p": ttest_p,
    }


def main() -> None:
    ensure_dirs()
    df = make_dataset()
    df.to_csv(DATA_DIR / "pdm_synthetic_sensor_data.csv", index=False)
    featured = add_features(df)
    featured.to_csv(DATA_DIR / "pdm_synthetic_features.csv", index=False)
    metrics = calculate_metrics(df)
    write_notebook()
    make_pdf(metrics)
    write_proposal(metrics)

    plt.figure(figsize=(8, 4))
    one_asset = featured[featured["asset_id"] == "PUMP-001"]
    plt.plot(one_asset["timestamp"], one_asset["vibration_g"], label="Raw vibration", alpha=0.55)
    plt.plot(one_asset["timestamp"], one_asset["vibration_rms_6"], label="6-window RMS")
    plt.title("PUMP-001 Vibration Degradation Signal")
    plt.ylabel("Vibration (g)")
    plt.xticks(rotation=30, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "pump_001_vibration_signal.png", dpi=160)


if __name__ == "__main__":
    main()
