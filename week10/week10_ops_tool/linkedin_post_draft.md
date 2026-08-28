I built **PumpGuard Ops** — an AI-assisted predictive-maintenance triage tool for operational pump fleets. 

Maintenance teams do not need another spreadsheet full of sensor readings. They need a
clear answer to: **Which asset should we investigate first?**

PumpGuard Ops turns time-series vibration, temperature, pressure, acoustic, motor-current,
and error-event data into:

- A prioritized 7-day failure-risk queue
- Normal, Watch, and Critical risk bands
- Per-pump model contribution summaries
- Asset telemetry trends and depot filters
- A downloadable maintenance action list

The tool uses Streamlit, XGBoost, SMOTE, grouped cross-validation, Docker, and a strict CSV
validation layer. It was developed through a Vibe Coding workflow with OpenAI Codex, and I
documented the key prompts and human review decisions in `PROMPTS.md`.

For the bundled 24-pump demonstration, prioritization takes under two minutes versus an
illustrative estimate of approximately 30 minutes for manual spreadsheet review. The
included data and performance are synthetic, so the next responsible step is validation
and calibration with real maintenance records and engineers.

Explore the code, tests, model card, and prompt log:
https://github.com/lameckirungu/plp_data/tree/main/week10/week10_ops_tool

Would a transparent risk queue help your maintenance team move from reactive work to
earlier intervention?

#PredictiveMaintenance #DataAnalytics #MachineLearning #Streamlit #XGBoost
#OperationalExcellence #VibeCoding #AI #AssetManagement #Python
