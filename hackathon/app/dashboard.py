"""Executive dashboard for the KPC order-to-cash leakage pipeline.

Run: streamlit run app/dashboard.py

Filters recompute KPIs by calling the same reconcile.overall_summary /
summarize_by functions the batch pipeline uses on a filtered slice of
data/processed/reconciled_order_to_cash.csv -- so a filtered dashboard
number and the pipeline's own JSON output can never silently disagree,
they are the same code path applied to a different row subset.
"""

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from o2c_pipeline.config import (  # noqa: E402
    DQ_ISSUES_LOG,
    LEAKAGE_SUMMARY_JSON,
    RECONCILED_OUTPUT,
)
from o2c_pipeline.pipeline import PIPELINE_RUN_LOG, run_pipeline  # noqa: E402
from o2c_pipeline.reconcile import LEAKAGE_CATEGORIES, overall_summary, summarize_by  # noqa: E402
from o2c_pipeline.report import CATEGORY_COLORS, CATEGORY_LABELS  # noqa: E402

st.set_page_config(
    page_title="KPC Order-to-Cash Leakage",
    page_icon="\U0001F6E2️",
    layout="wide",
)

SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRIDLINE = "#e1e0d9"
MAGNITUDE_BLUE = "#2a78d6"
STATUS_GOOD = "#0ca30c"
STATUS_CRITICAL = "#d03b3b"

PLOTLY_LAYOUT = dict(
    paper_bgcolor=SURFACE,
    plot_bgcolor=SURFACE,
    font=dict(color=INK_SECONDARY, family="system-ui, -apple-system, Segoe UI, sans-serif"),
    margin=dict(l=10, r=10, t=40, b=10),
)


@st.cache_data(ttl=5)
def load_summary() -> dict:
    with open(LEAKAGE_SUMMARY_JSON) as f:
        return json.load(f)


@st.cache_data(ttl=5)
def load_reconciled() -> pd.DataFrame:
    df = pd.read_csv(RECONCILED_OUTPUT, parse_dates=["loading_ts", "dispatch_ts", "invoice_date"])
    return df


@st.cache_data(ttl=5)
def load_dq_issues() -> pd.DataFrame:
    if not DQ_ISSUES_LOG.exists():
        return pd.DataFrame(columns=["table", "check", "severity", "count", "detail"])
    return pd.read_csv(DQ_ISSUES_LOG)


def load_run_log() -> dict:
    if not PIPELINE_RUN_LOG.exists():
        return {}
    with open(PIPELINE_RUN_LOG) as f:
        return json.load(f)


def fmt_kes(value: float) -> str:
    if abs(value) >= 1e9:
        return f"KES {value / 1e9:,.2f}B"
    return f"KES {value / 1e6:,.1f}M"


def render_sidebar(reconciled: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.title("Filters")

    depots = sorted(reconciled["depot"].dropna().unique())
    products = sorted(reconciled["product"].dropna().unique())

    selected_depots = st.sidebar.multiselect("Depot", depots, default=depots)
    selected_products = st.sidebar.multiselect("Product", products, default=products)

    min_date = reconciled["loading_ts"].min().date()
    max_date = reconciled["loading_ts"].max().date()
    date_range = st.sidebar.slider(
        "Loading date range", min_value=min_date, max_value=max_date,
        value=(min_date, max_date),
    )

    customer_search = st.sidebar.text_input("Customer contains", "")

    st.sidebar.divider()
    st.sidebar.subheader("Pipeline")
    run_log = load_run_log()
    if run_log:
        status = run_log.get("status", "UNKNOWN")
        badge = "\U0001F7E2" if status == "SUCCESS" else "\U0001F534"
        st.sidebar.markdown(f"{badge} **Last run:** {status}")
        st.sidebar.caption(f"{run_log.get('run_at', '')}  ·  {run_log.get('duration_seconds', '?')}s")
        st.sidebar.caption(f"Quality gate: {run_log.get('quality_gate_status', '?')}")
    if st.sidebar.button("\U0001F504 Re-run pipeline now", width="stretch"):
        with st.spinner("Running ingest -> clean -> quality gate -> reconcile..."):
            run_pipeline(strict=False)
        st.cache_data.clear()
        st.rerun()

    mask = (
        reconciled["depot"].isin(selected_depots)
        & reconciled["product"].isin(selected_products)
        & (reconciled["loading_ts"].dt.date >= date_range[0])
        & (reconciled["loading_ts"].dt.date <= date_range[1])
    )
    if customer_search:
        mask &= reconciled["customer"].str.contains(customer_search, case=False, na=False)

    return reconciled[mask].copy()


def render_kpi_row(filtered: pd.DataFrame, run_log: dict) -> dict:
    summary = overall_summary(filtered)
    cols = st.columns(5)
    cols[0].metric("Total leakage", fmt_kes(summary["total_leakage_kes"]))
    cols[1].metric("% of expected revenue", f"{summary['leakage_pct_of_expected_revenue']:.1f}%")
    cols[2].metric("Exception rate", f"{summary['exception_rate_pct']:.1f}%",
                    help=f"{summary['exception_count']} of {summary['total_loadings']} loadings")
    cols[3].metric("Annualized leakage", fmt_kes(summary["annualized_leakage_kes"]))
    gate_status = run_log.get("quality_gate_status", "N/A")
    cols[4].metric("Data-quality gate", gate_status)
    return summary


def render_overview_tab(filtered: pd.DataFrame, summary: dict) -> None:
    left, right = st.columns(2)

    with left:
        by_cat = summary["leakage_by_category_kes"]
        cat_df = pd.DataFrame({
            "category": [CATEGORY_LABELS[c] for c in LEAKAGE_CATEGORIES],
            "amount": [by_cat[c] for c in LEAKAGE_CATEGORIES],
            "color": [CATEGORY_COLORS[c] for c in LEAKAGE_CATEGORIES],
        }).sort_values("amount")
        fig = go.Figure(go.Bar(
            x=cat_df["amount"], y=cat_df["category"], orientation="h",
            marker_color=cat_df["color"],
            text=[fmt_kes(v) for v in cat_df["amount"]], textposition="outside",
            hovertemplate="%{y}: %{text}<extra></extra>",
        ))
        fig.update_layout(title="Leakage by category", **PLOTLY_LAYOUT)
        fig.update_xaxes(showgrid=True, gridcolor=GRIDLINE, title=None)
        st.plotly_chart(fig, width="stretch")

    with right:
        by_depot = summarize_by(filtered, "depot")
        fig = go.Figure(go.Bar(
            x=by_depot["total_leakage_kes"], y=by_depot["depot"], orientation="h",
            marker_color=MAGNITUDE_BLUE,
            text=[fmt_kes(v) for v in by_depot["total_leakage_kes"]], textposition="outside",
            hovertemplate="%{y}: %{text}<extra></extra>",
        ))
        fig.update_layout(title="Leakage by depot", **PLOTLY_LAYOUT)
        fig.update_yaxes(autorange="reversed")
        fig.update_xaxes(showgrid=True, gridcolor=GRIDLINE, title=None)
        st.plotly_chart(fig, width="stretch")

    left2, right2 = st.columns(2)

    with left2:
        daily = (
            filtered.dropna(subset=["loading_ts"])
            .assign(day=filtered["loading_ts"].dt.date)
            .groupby("day")["total_leakage_kes"].sum().reset_index()
        )
        fig = px.area(daily, x="day", y="total_leakage_kes")
        fig.update_traces(line_color=MAGNITUDE_BLUE, fillcolor="rgba(42,120,214,0.12)")
        fig.update_layout(title="Daily leakage trend", **PLOTLY_LAYOUT)
        fig.update_yaxes(showgrid=True, gridcolor=GRIDLINE, title=None)
        fig.update_xaxes(title=None)
        st.plotly_chart(fig, width="stretch")

    with right2:
        by_cust = summarize_by(filtered, "customer").head(8).sort_values("total_leakage_kes")
        fig = go.Figure(go.Bar(
            x=by_cust["total_leakage_kes"], y=by_cust["customer"], orientation="h",
            marker_color=MAGNITUDE_BLUE,
            text=[fmt_kes(v) for v in by_cust["total_leakage_kes"]], textposition="outside",
            hovertemplate="%{y}: %{text}<extra></extra>",
        ))
        fig.update_layout(title="Top customers by leakage exposure", **PLOTLY_LAYOUT)
        fig.update_xaxes(showgrid=True, gridcolor=GRIDLINE, title=None)
        st.plotly_chart(fig, width="stretch")


def render_exceptions_tab(filtered: pd.DataFrame, summary: dict) -> None:
    st.markdown("#### Executive narrative")
    st.markdown(summary["executive_narrative"])

    st.markdown("#### Exceptions / audit trail")
    exceptions = filtered[filtered["is_exception"]].sort_values("total_leakage_kes", ascending=False)
    st.caption(f"{len(exceptions):,} exceptions in the current filter selection")

    display_cols = [
        "loading_id", "depot", "product", "customer", "leakage_category",
        "total_leakage_kes", "dispatch_capture_gap_kes", "shrinkage_kes",
        "billing_gap_kes", "underbilling_kes", "collections_gap_kes",
    ]
    st.dataframe(
        exceptions[display_cols].head(500),
        width="stretch", height=400,
    )
    st.download_button(
        "Download full exceptions CSV",
        exceptions.to_csv(index=False).encode("utf-8"),
        file_name="o2c_exceptions.csv", mime="text/csv",
    )


def render_roi_tab(summary: dict) -> None:
    roi = summary.get("roi")
    if not roi:
        st.info("Run the pipeline at least once to compute an ROI estimate.")
        return

    st.warning(roi["note"])

    cols = st.columns(4)
    cols[0].metric("Year-1 build cost", fmt_kes(roi["implementation_cost_kes"]))
    cols[1].metric("Year-1 realized benefit", fmt_kes(roi["year1_realized_benefit_kes"]),
                    help=f"{roi['year1_adoption_ramp_factor']:.0%} of full network live in year one")
    cols[2].metric("Payback period", f"{roi['payback_period_months']:.1f} months")
    cols[3].metric("Year-1 ROI multiple", f"{roi['roi_multiple_year1']:.1f}x")

    steady_state = fmt_kes(roi["steady_state_recoverable_annual_kes"])
    st.markdown(f"**Steady-state annual recovery (full network live):** {steady_state}")

    breakdown = pd.DataFrame(roi["category_breakdown"])
    breakdown["category"] = breakdown["category"].map(CATEGORY_LABELS)
    breakdown["annualized_leakage_kes"] = breakdown["annualized_leakage_kes"].map(fmt_kes)
    breakdown["recoverable_kes"] = breakdown["recoverable_kes"].map(fmt_kes)
    breakdown["recovery_rate"] = breakdown["recovery_rate"].map(lambda r: f"{r:.0%}")
    st.dataframe(
        breakdown.rename(columns={
            "category": "Category", "annualized_leakage_kes": "Annualized leakage",
            "recovery_rate": "Recovery rate", "recoverable_kes": "Recoverable/year",
            "rationale": "Why this rate",
        }),
        width="stretch", hide_index=True,
    )


def render_data_quality_tab(summary: dict, dq_issues: pd.DataFrame) -> None:
    dq = summary.get("data_quality", {})
    status = dq.get("overall_status", "N/A")
    color = STATUS_GOOD if status == "PASS" else STATUS_CRITICAL
    st.markdown(f"### Gate status: <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)

    checks = pd.DataFrame(dq.get("checks", []))
    if not checks.empty:
        st.dataframe(checks, width="stretch", hide_index=True)

    st.markdown("#### Cleaning issues log")
    st.caption("'critical' issues would fail the gate above threshold; 'warning' and 'exception' never do.")
    st.dataframe(dq_issues, width="stretch", hide_index=True)


def main() -> None:
    st.title("\U0001F6E2️ KPC Order-to-Cash Leakage")
    st.caption("Reconciling loading -> dispatch -> invoice -> payment to close revenue-leakage gaps")

    if not RECONCILED_OUTPUT.exists():
        st.warning("No pipeline output found yet.")
        if st.button("Run pipeline now"):
            with st.spinner("Running pipeline..."):
                run_pipeline(strict=False)
            st.rerun()
        return

    reconciled = load_reconciled()
    dq_issues = load_dq_issues()
    run_log = load_run_log()

    filtered = render_sidebar(reconciled)
    if filtered.empty:
        st.warning("No rows match the current filters.")
        return

    summary = render_kpi_row(filtered, run_log)
    # Reuse the pipeline's own by-depot/by-customer for the ROI/narrative
    # panels so filtered-view text and unfiltered headline figures are both
    # available without recomputation drift.
    full_summary = load_summary()

    tab_overview, tab_exceptions, tab_roi, tab_dq = st.tabs(
        ["Overview", "Exceptions & Audit Trail", "ROI & Business Case", "Data Quality"]
    )
    with tab_overview:
        render_overview_tab(filtered, summary)
    with tab_exceptions:
        render_exceptions_tab(filtered, full_summary)
    with tab_roi:
        render_roi_tab(full_summary)
    with tab_dq:
        render_data_quality_tab(full_summary, dq_issues)


if __name__ == "__main__":
    main()
