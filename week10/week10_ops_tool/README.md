# PumpGuard Ops

PumpGuard Ops is an AI-assisted Streamlit tool that converts pump telemetry into a
prioritized 7-day maintenance-risk queue. It extends the predictive-maintenance capstone
from Weeks 6 and 9 into a workflow an operations team can actually use: load telemetry,
identify the assets to review first, inspect the model's main risk contributions, and
export an action list.

> **Portfolio demonstration:** the included telemetry is physics-informed and synthetic.
> Metrics and recommendations are not validated Kenya Pipeline Company production results.

## Operational problem and value

Manual spreadsheet review makes it slow to compare many pumps and easy to miss the
combination of rising vibration, heat, current, and error activity. PumpGuard scores the
latest reading for each asset consistently and keeps the underlying evidence visible.

For the bundled 24-pump scenario, the intended workflow is under two minutes versus an
illustrative 30-minute manual review. This is a demo assumption, not a measured
organizational baseline; validate it with users before presenting it as realized savings.

## Features

- Bundled 24-pump demo or validated CSV upload
- Six-reading rolling vibration and temperature features
- XGBoost + SMOTE model with leakage-safe grouped cross-validation
- Operationally tuned threshold (81.5% recall, 2.7% false-positive rate on synthetic
  out-of-fold predictions; ROC-AUC 0.943)
- Normal, Watch, and Critical queue with human-review actions
- Per-asset XGBoost contribution summary and telemetry drill-down
- Depot/risk filters, visual comparisons, CSV template, and queue export
- Model governance card and synthetic-data warnings
- Local, Docker, and Streamlit Community Cloud run paths

## Run locally

Python 3.12 is recommended.

```bash
cd week10/week10_ops_tool
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env                 # optional; .env is ignored by git
.venv/bin/streamlit run app.py
```

Open `http://localhost:8501`. No API key or external model service is required.

## Run with Docker

```bash
cd week10/week10_ops_tool
docker compose up --build
```

The container exposes `http://localhost:8501` and includes a Streamlit health check.
The image uses `python:3.12-slim`, CPU-only XGBoost, and a cache-free pip install to avoid
shipping GPU libraries or duplicate wheel caches.

### Dependency footprint

Measured on Linux x86-64 with Python 3.12 and the pinned production requirements:

| Footprint | Download | Installed disk |
|---|---:|---:|
| ML stack: NumPy, SciPy, scikit-learn, imbalanced-learn, CPU XGBoost and helpers | 67.6 MB | 282.7 MB |
| Complete production Python dependency set, including Streamlit | 162.3 MB | 647.6 MB |

CPU-only XGBoost itself is 5.8 MB downloaded and 24.5 MB installed. The full runtime is
larger mainly because Streamlit requires PyArrow and scikit-learn requires NumPy/SciPy.
Plotly and SHAP are deliberately omitted; charts use Streamlit's existing Altair dependency.
Docker adds the `python:3.12-slim` operating-system and interpreter layers, while
`--no-cache-dir` prevents the 162.3 MB wheel download set from being stored a second time.

## Deploy to Streamlit Community Cloud

1. Push this folder to GitHub.
2. In Streamlit Community Cloud, select this repository and set the main file to
   `week10/week10_ops_tool/app.py`.
3. Use Python 3.12. No secrets are required for the bundled configuration.

Relative data paths are resolved from the tool directory, so the app does not depend on a
developer's machine path.

## CSV input contract

Each row is one time-stamped sensor observation. At least six chronological observations
per pump are recommended; shorter histories work but produce a warning.

| Column | Meaning |
|---|---|
| `timestamp` | ISO or day-first observation date/time |
| `asset_id` | Stable pump identifier |
| `depot` | Operating location; unseen values are supported |
| `shift` | `Day` or `Night` |
| `asset_age_months` | Non-negative asset age |
| `vibration_g` | Vibration measurement |
| `temperature_c` | Temperature in Celsius |
| `pressure_psi` | Operating pressure |
| `acoustic_db` | Acoustic level |
| `motor_current_a` | Motor current |
| `error_events` | Error-event count |

The app rejects missing columns, invalid timestamps/numbers, negative values, unsupported
shift names, and duplicate asset/timestamp pairs with actionable messages. Outcome fields
such as `failure_within_7_days`, `health_status`, `fault_type`, and
`time_to_failure_hours` are ignored during scoring to prevent leakage.

## Model methodology

Training uses 2,496 historical readings from 24 synthetic pumps. The 144 demo rows are
held out of training. Rolling features are computed inside the tool, so training and
uploaded data follow the same transformation.

Threshold evaluation uses stratified grouped cross-validation: all readings for a pump
stay in one fold. From thresholds 0.05–0.95, the tool maximizes F1 among candidates with at
least 80% recall and no more than 5% false-positive rate. The selected threshold is 0.67.
The final model is refit on all historical training rows and cached for the Streamlit
session. Risk bands are policy aids, not automatic shutdown commands.

## Tests

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

The suite covers validation failures, rolling-window isolation, target leakage, model
determinism, scoring completeness, explanations, and a Streamlit bundled-demo smoke test.

## Security and limitations

- `.env` is ignored; only `.env.example` is committed.
- The application makes no outbound API calls and contains no hardcoded credentials.
- Uploaded files are processed in memory and are not persisted by application code.
- Synthetic performance does not establish production accuracy, calibration, or safety.
- Production adoption requires real maintenance labels, access control, audit logging,
  drift monitoring, calibration, and engineering approval.

The AI-assisted development evidence is in [PROMPTS.md](PROMPTS.md). The Week 10 capstone
reflection, demo script, and LinkedIn draft are included alongside the application.
