"""FastAPI service for the KPC order-to-cash leakage dashboard.

Run: uvicorn api.main:app --reload --port 8000

In production (the Docker image) this same app also serves the built
React frontend as static files, so the whole thing ships as one
container/process rather than two services that have to agree on a URL.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api import data
from o2c_pipeline.pipeline import run_pipeline
from o2c_pipeline.reconcile import overall_summary, summarize_by

app = FastAPI(
    title="KPC Order-to-Cash Leakage API",
    description="Reconciliation findings, exceptions, and ROI for Inuka Hackathon Problem 7D",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # internal analytics tool, no auth/secrets in play
    allow_methods=["*"],
    allow_headers=["*"],
)


def _filtered_reconciled(
    depot: list[str] | None,
    product: list[str] | None,
    customer: str | None,
    start_date: str | None,
    end_date: str | None,
    exceptions_only: bool = False,
):
    try:
        df = data.load_reconciled()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return data.apply_filters(df, depot, product, customer, start_date, end_date, exceptions_only)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/meta")
def meta():
    return data.load_run_log()


@app.get("/api/filters/options")
def filter_options():
    df = data.load_reconciled()
    return {
        "depots": sorted(df["depot"].dropna().unique().tolist()),
        "products": sorted(df["product"].dropna().unique().tolist()),
        "min_date": df["loading_ts"].min().date().isoformat(),
        "max_date": df["loading_ts"].max().date().isoformat(),
    }


@app.get("/api/kpis")
def kpis(
    depot: list[str] | None = Query(default=None),
    product: list[str] | None = Query(default=None),
    customer: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    filtered = _filtered_reconciled(depot, product, customer, start_date, end_date)
    if filtered.empty:
        raise HTTPException(status_code=404, detail="No rows match the given filters")

    summary = overall_summary(filtered)
    summary["by_depot"] = summarize_by(filtered, "depot").to_dict(orient="records")
    summary["by_product"] = summarize_by(filtered, "product").to_dict(orient="records")
    summary["by_customer"] = summarize_by(filtered, "customer").head(10).to_dict(orient="records")
    return summary


@app.get("/api/trend")
def trend(
    depot: list[str] | None = Query(default=None),
    product: list[str] | None = Query(default=None),
    customer: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    filtered = _filtered_reconciled(depot, product, customer, start_date, end_date)
    daily = (
        filtered.dropna(subset=["loading_ts"])
        .assign(day=filtered["loading_ts"].dt.date.astype(str))
        .groupby("day")["total_leakage_kes"].sum()
        .reset_index()
    )
    return daily.to_dict(orient="records")


@app.get("/api/exceptions")
def exceptions(
    depot: list[str] | None = Query(default=None),
    product: list[str] | None = Query(default=None),
    customer: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 200,
    offset: int = 0,
):
    filtered = _filtered_reconciled(
        depot, product, customer, start_date, end_date, exceptions_only=True
    )
    filtered = filtered.sort_values("total_leakage_kes", ascending=False)
    total = len(filtered)
    page = filtered.iloc[offset : offset + limit]

    cols = [
        "loading_id", "depot", "product", "customer", "leakage_category",
        "total_leakage_kes", "dispatch_capture_gap_kes", "shrinkage_kes",
        "billing_gap_kes", "underbilling_kes", "collections_gap_kes",
        "loading_ts",
    ]
    page = page[cols].copy()
    page["loading_ts"] = page["loading_ts"].astype(str)

    return {"total": total, "offset": offset, "limit": limit, "rows": page.to_dict(orient="records")}


@app.get("/api/roi")
def roi():
    try:
        summary = data.load_summary()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return summary.get("roi", {})


@app.get("/api/narrative")
def narrative():
    try:
        summary = data.load_summary()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "executive_narrative": summary.get("executive_narrative", ""),
        "alert_narratives": summary.get("alert_narratives", []),
    }


@app.get("/api/data-quality")
def data_quality():
    try:
        summary = data.load_summary()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    issues = data.load_dq_issues()
    dq = summary.get("data_quality", {})
    return {
        "overall_status": dq.get("overall_status", "N/A"),
        "checks": dq.get("checks", []),
        "issues": issues.to_dict(orient="records"),
    }


@app.post("/api/pipeline/run")
def trigger_pipeline_run():
    try:
        summary = run_pipeline(strict=False)
    except Exception as exc:  # noqa: BLE001 -- surface any failure to the caller as a 500
        raise HTTPException(status_code=500, detail=f"Pipeline run failed: {exc}") from exc
    return {"status": "ok", "quality_gate_status": summary["data_quality"]["overall_status"]}


# Serve the built frontend (production/Docker only -- absent in local dev,
# where the Vite dev server handles the frontend instead).
_frontend_dist = Path(__file__).resolve().parents[1] / "web" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
