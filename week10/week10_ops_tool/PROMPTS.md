# PumpGuard Ops — Vibe Coding Prompt Log

**AI assistant used:** OpenAI Codex  
**Development date:** 28 August 2026  
**Human owner/reviewer:** Lameck Mugo

This is a concise record of the key prompts and decisions used to build the tool. It is
not a claim that AI output was accepted blindly: generated code was inspected, tested,
and revised against the operational requirements.

## 1. Assignment framing

> Create a functional tool in the GitHub repo named `week10_ops_tool`. Choose an
> automation script, chatbot/RAG app, or enhanced Streamlit dashboard. Include AI prompt
> evidence, no hardcoded secrets, a working operational use case, a three-minute product
> demo, LinkedIn draft, and `capstone_week10_update.md`. First explain what you understand
> and create a logical step-by-step implementation plan.

**Used for:** decomposing the rubric and identifying a dashboard that could extend the
existing predictive-maintenance capstone rather than creating an unrelated Week 10 demo.

## 2. Product and architecture decision

> Plan an enhanced Streamlit “Pump Maintenance Triage” dashboard in
> `week10/week10_ops_tool`. Reuse the existing pump telemetry and Week 9 ML direction.
> Support a bundled sample plus CSV upload, produce a 7-day failure-risk queue, explanations,
> filters, and export. Brand it PumpGuard Ops and keep KPC as a clearly synthetic scenario.

**Used for:** the app navigation, operational queue, asset drill-down, model card, and
local/Docker/cloud-ready packaging.

## 3. Leakage-safe ML prompt

> Turn the notebook prototype into reusable model code. Do not allow target proxies such
> as failure label, health status, fault type, or time-to-failure into the features. Keep
> each asset in one evaluation fold, place SMOTE inside the training pipeline, tune the
> threshold for at least 80% recall and at most 5% false-positive rate, and disclose a
> fallback when the constraints are infeasible.

**Used for:** the grouped cross-validation pipeline, threshold policy, exclusion tests,
and model governance card. This refinement corrected the common AI tendency to use a
random row split, which would overstate time-series performance.

## 4. Upload and feature-engineering prompt

> Define one explicit raw CSV contract and compute six-reading rolling features inside the
> tool so uploaded and training data use identical transformations. Reject malformed dates,
> nonnumeric or negative sensor values, missing required columns, and duplicate
> asset/timestamp rows with actionable messages. Accept unseen depots safely.

**Used for:** telemetry validation, rolling vibration/temperature features, CSV template,
and malformed-input test cases.

## 5. Explainability and UX prompt

> Give maintenance users the latest score per pump, a Normal/Watch/Critical band, a review
> timeframe, and the three largest positive model contributions. Explain that contributions
> are model reasoning rather than physical causality. Add depot filters, queue export,
> telemetry trends, and prominent synthetic-data/human-review warnings.

**Used for:** XGBoost contribution extraction, friendly driver names, queue actions,
dashboard filters, and the asset-detail experience.

## 6. Security and dependency-size prompt

> Keep secrets out of source control, load optional configuration from `.env`, commit only
> `.env.example`, and avoid unnecessary network services. Minimize Docker size: use a slim
> Python image, CPU-only XGBoost, no SHAP dependency, no pip cache, and report measured
> download and final image sizes.

**Used for:** environment configuration, offline runtime, Docker packaging, and replacing
the full XGBoost distribution with `xgboost-cpu`. XGBoost's built-in contribution output
removed the need for the heavier SHAP package.

## 7. Verification prompt

> Test schema validation, duplicate detection, rolling features per asset, leakage
> exclusion, deterministic training, threshold selection, complete scoring output, local
> explanations, the bundled demo, and a Streamlit application smoke run. Then build the
> Docker image and verify the health endpoint.

**Used for:** the pytest suite and final local/container acceptance checks. The first smoke
test exposed a missing pressure value in the bundled demo; the data preparation step was
then updated to make demo rows conform to the same strict upload contract.

## Human review decisions

- Selected an enhanced dashboard over a chatbot to avoid a paid API and keep the use case
  directly tied to the capstone.
- Required explicit synthetic-data language rather than presenting generated results as KPC facts.
- Chose a conservative, labeled time-saving estimate instead of claiming measured savings.
- Required Docker as well as local and cloud-ready operation.
- Retained human approval as the final maintenance decision.
