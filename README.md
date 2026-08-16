# Data Analytics Fellowship

**Programme:** PLP Data Analytics (Inuka / E&M Tech)
**Cohort:** 2026
**Focus:** Operational Data Analytics using Python, with Oil & Gas (Kenya Pipeline Company) as the primary teaching environment.

---

## About This Repository

This repository contains all project work completed during the 12-week Data Analytics Fellowship. Each week has its own folder containing the Jupyter Notebook (technical deliverable) and the accompanying business memo (soft skills deliverable).

The skills developed here are industry-agnostic — the same logic applied to pipeline operations translates directly to hospital patient flow, bank transaction monitoring, and retail supply chain management.

Alongside the weekly coursework, `hackathon/` holds my submission to the **Inuka Hackathon** — a full order-to-cash revenue-leakage reconciliation pipeline with a FastAPI backend and React dashboard, built on the same KPC operational domain. See [Capstone: Inuka Hackathon](#capstone-inuka-hackathon) below.

---

## Repository Structure

```
plp_data/
├── week1/      Intro to Operational Data Analytics & Python Essentials
├── week2/      Data Wrangling with Pandas & Operational Data Structures
├── week3/      Data Sourcing, APIs & Databases for Operational Environments
├── week4/      Data Engineering Pipelines — ETL, Automation & Quality
├── week5/      Exploratory Data Analysis (EDA) & Operational Diagnostics
├── week6/      Statistical Foundations & Predictive Maintenance (PdM)
├── week7/      Safety, Compliance & Environmental Analytics + Dashboarding
├── week8/      Supply Chain & Logistics Analytics + Data Storytelling
├── week9/      Machine Learning for Operational Predictions
├── week10/     Vibe Coding — AI-Assisted Operational Tools
├── week11/     Analytics Strategy, ROI & Professional Readiness
├── week12/     Capstone Showcase
├── hackathon/  Inuka Hackathon capstone — O2C leakage reconciliation pipeline + dashboard
└── assets/     Shared datasets, reference files, and resources
```

---

## Week Summaries

| Week | Topic | Notebook | Memo |
|------|-------|----------|------|
| 1 | Operational KPIs, Python functions, status classifiers | [week1_ops_analyzer.ipynb](week1/week1_ops_analyzer.ipynb) | [Week1_Memo_Lameck.pdf](week1/Week1_Memo_Lameck_.pdf) |
| 2 | Data wrangling with Pandas/NumPy — cleaning messy sensor, retail, and hospital datasets | [week2_data_wrangler.ipynb](week2/week2_data_wrangler.ipynb) | [Week2_Insight_Report_Lameck.pdf](week2/Week2_Insight_Report_Lameck.pdf) |
| 3 | Multi-source sourcing (CSV, API, DB) — rainfall vs. flow-rate correlation study | [week3_multi_source_pipeline.ipynb](week3/week3_multi_source_pipeline.ipynb) | [Week3_LightningTalk_Lameck.pdf](week3/Week3_LightningTalk_Lameck.pdf) |
| 4 | *(not yet submitted)* | — | — |
| 5 | Exploratory data analysis & operational diagnostics | [week5_diagnostics_analysis.ipynb](week5/week5_diagnostics_analysis.ipynb) | [Week5_Diagnostics_Report_Lameck.pdf](week5/Week5_Diagnostics_Report_Lameck.pdf) |
| 6 | Statistical validation, feature engineering & predictive maintenance (logistic + linear regression) | [week6_stats_and_pdm.ipynb](week6/week6_stats_and_pdm.ipynb) | [Week6_Communication_Briefs_Lameck.pdf](week6/Week6_Communication_Briefs_Lameck.pdf) |
| 7 | Safety Command Center — Streamlit dashboard over 445 real HSE incident records | [app_safety_dashboard.py](week7/app_safety_dashboard.py) | [Week7_Safety_Alert_Lameck.pdf](week7/Week7_Safety_Alert_Lameck.pdf) |
| 8 | Supply chain & logistics optimization, data storytelling | [week8_supply_chain_optimization.ipynb](week8/week8_supply_chain_optimization.ipynb) | [Week8_Ops_Review_Lameck.pdf](week8/Week8_Ops_Review_Lameck.pdf) |
| 9–12 | *(in progress)* | — | — |

---

## Capstone: Inuka Hackathon

**[`hackathon/`](hackathon/)** — KPC Order-to-Cash Leakage Reconciliation, my submission to the
Inuka Hackathon (Domain D: Revenue Assurance, Billing & Reconciliation). It reconciles product
loading → dispatch → invoice → payment events and quantifies, in Kenyan shillings, exactly where
order-to-cash revenue leaks.

Unlike the week folders, this is a real multi-service application:

- **`src/o2c_pipeline/`** — a Python ETL pipeline (ingest → clean → data-quality gate → reconcile
  → ROI → narrative → report) with a pandera-backed quality gate and pytest coverage.
- **`api/`** — a FastAPI backend exposing the reconciliation output as JSON.
- **`web/`** — a React + TypeScript + Tailwind + Recharts dashboard with live filters, an
  exceptions/audit-trail view, and an ROI/business-case tab.
- CI (lint, test, data-quality gate, frontend build) and a Docker image that serves both API and
  frontend from one container.

See [`hackathon/README.md`](hackathon/README.md) for architecture, findings, and how to run it.

---

## Tools & Environment

- **Language:** Python 3.11+
- **Environment:** Anaconda Distribution / Jupyter Lab
- **IDE:** VS Code with Python & Jupyter extensions
- **Version Control:** Git / GitHub
- **Key Libraries:** pandas, numpy, matplotlib, scikit-learn, streamlit, fastapi *(added progressively)*

---

## Deliverable Format

Each week produces two outputs:

1. **Jupyter Notebook** — technical implementation with documented code and markdown explanations aimed at junior analysts.
2. **PDF Memo** — a one-page business communication translating the technical findings for non-technical senior stakeholders.

---

*Lameck Irungu — Data & Systems Analyst | Nairobi, Kenya*
