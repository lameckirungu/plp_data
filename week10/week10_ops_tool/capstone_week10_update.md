# Capstone Week 10 Update — Lameck Mugo

## How did AI accelerate my Capstone development this week?

AI accelerated the move from a Week 9 experimental notebook to a usable operational
product. It helped decompose the notebook into reusable validation, feature-engineering,
training, scoring, explanation, and interface layers; generated an initial Streamlit and
Docker structure; and proposed test cases for malformed telemetry and model leakage.

The acceleration came from shortening the build-review loop, not from replacing review.
I checked the generated logic against the existing capstone data, ran the complete test
suite, inspected the selected operating threshold, and revised outputs that were not
operationally credible.

## What specific feature did I build using Vibe Coding?

I built **PumpGuard Ops**, a Streamlit predictive-maintenance triage tool. It accepts
time-series pump telemetry, computes rolling sensor features, and uses an XGBoost + SMOTE
pipeline to estimate failure risk within seven days. Maintenance users receive a
prioritized queue, risk bands, recommended review timeframes, model contributions, asset
telemetry trends, depot filters, and a downloadable action list.

The tool integrates the capstone directly: it reuses the synthetic pump fleet developed
in Week 6 and the ensemble-model/threshold approach developed in Week 9. The current
synthetic grouped evaluation achieved ROC-AUC 0.943, recall 81.5%, and a 2.7%
false-positive rate at a 0.67 threshold. These figures demonstrate the workflow and are
not claims of KPC production performance.

## What prompting challenge did I face, and how did I overcome it?

My first broad prompting direction could have produced an attractive dashboard with an
unreliable model. Predictive-maintenance data contains repeated readings for each pump,
and a normal random row split can place the same pump in both training and validation.
Outcome-like columns such as health status and time-to-failure can also leak the answer.

I overcame this by making the prompt testable and explicit: keep every asset in one
evaluation fold, exclude named outcome proxies, compute rolling features through one
shared function, put SMOTE inside the pipeline, and add tests proving those constraints.
This changed AI from a general code generator into a collaborator working against a clear
operational and methodological contract.
