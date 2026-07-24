"""Executive narrative + per-exception audit-alert text generation.

Deliberately template-based rather than an LLM call: a live judging demo
cannot depend on network access or an API key being present, and the
numbers driving every sentence here come straight out of the
reconciliation, so a deterministic renderer is more trustworthy for an
audit trail than a paraphrasing model would be. (`generate_alert_narratives`
is the natural place to swap in an LLM call for richer prose later --
the function boundary already isolates "which facts" from "how to phrase
them.")
"""

import pandas as pd

CATEGORY_LABELS = {
    "dispatch_capture_gap_kes": "dispatch capture gaps",
    "shrinkage_kes": "in-transit shrinkage",
    "billing_gap_kes": "billing gaps",
    "underbilling_kes": "underbilling",
    "collections_gap_kes": "collections shortfalls",
}

CATEGORY_ACTIONS = {
    "dispatch_capture_gap_kes": "Automate gate/dispatch confirmation capture so every loading "
                                 "has a matching dispatch record before it can be closed out.",
    "shrinkage_kes": "Audit meter calibration and transit routes for the affected depots; "
                      "material losses above tolerance warrant a physical investigation.",
    "billing_gap_kes": "Add a same-day dispatch-to-invoice matching check so no confirmed "
                        "dispatch goes unbilled past 24 hours.",
    "underbilling_kes": "Add an automated volume cross-check between dispatch and invoice "
                         "before an invoice is released.",
    "collections_gap_kes": "Introduce automated AR aging alerts and a dunning workflow for "
                            "invoices unpaid beyond terms.",
}


def _fmt_kes(value: float) -> str:
    if abs(value) >= 1e9:
        return f"KES {value / 1e9:,.2f}B"
    return f"KES {value / 1e6:,.1f}M"


def generate_executive_narrative(summary: dict, roi: dict) -> str:
    by_cat = summary["leakage_by_category_kes"]
    ranked = sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)
    top_cat, top_cat_amount = ranked[0]
    second_cat, second_cat_amount = ranked[1]

    top_depot = max(summary["by_depot"], key=lambda r: r["total_leakage_kes"])
    top_customer = max(summary["by_customer"], key=lambda r: r["total_leakage_kes"])

    lines = []
    lines.append(
        f"Over a {summary['simulation_window_days']}-day operating window, KPC's order-to-cash "
        f"cycle leaked {_fmt_kes(summary['total_leakage_kes'])} against "
        f"{_fmt_kes(summary['total_expected_revenue_kes'])} of expected ex-depot revenue -- "
        f"{summary['leakage_pct_of_expected_revenue']:.1f}% of value shipped never converts to "
        f"collected cash. Annualized, that is approximately "
        f"{_fmt_kes(summary['annualized_leakage_kes'])} at current throughput."
    )
    lines.append(
        f"The largest driver is **{CATEGORY_LABELS[top_cat]}** at {_fmt_kes(top_cat_amount)}, "
        f"followed by **{CATEGORY_LABELS[second_cat]}** at {_fmt_kes(second_cat_amount)}. "
        f"{summary['exception_count']} of {summary['total_loadings']} loadings "
        f"({summary['exception_rate_pct']:.1f}%) carry at least one reconciliation exception."
    )
    lines.append(
        f"Leakage concentrates geographically and commercially: {top_depot['depot']} depot alone "
        f"accounts for {_fmt_kes(top_depot['total_leakage_kes'])}, and {top_customer['customer']} "
        f"is the single largest customer-level exposure at {_fmt_kes(top_customer['total_leakage_kes'])}. "
        f"This concentration means targeted intervention -- not a broad program -- closes most of the gap."
    )
    lines.append(
        f"Recommended near-term actions, in priority order: "
        f"(1) {CATEGORY_ACTIONS[top_cat]} "
        f"(2) {CATEGORY_ACTIONS[second_cat]}"
    )
    lines.append(
        f"Business case (phased rollout, {roi['year1_adoption_ramp_factor']:.0%} of full network "
        f"live in year one): {_fmt_kes(roi['year1_realized_benefit_kes'])} recovered against an "
        f"estimated {_fmt_kes(roi['implementation_cost_kes'])} year-one build cost -- payback in "
        f"{roi['payback_period_months']:.1f} months, a {roi['roi_multiple_year1']:.1f}x first-year "
        f"return. At steady state (full network live), the same recovery assumptions imply "
        f"{_fmt_kes(roi['steady_state_recoverable_annual_kes'])} per year."
    )
    lines.append(f"*Note: {roi['note']}*")
    return "\n\n".join(lines)


def generate_alert_narratives(reconciled: pd.DataFrame, top_n: int = 15) -> list[dict]:
    """One audit-note per top exception, ranked by KES exposure -- the raw
    material for an exceptions/audit-trail view."""
    exceptions = reconciled[reconciled["is_exception"]].copy()
    if exceptions.empty:
        return []
    exceptions = exceptions.sort_values("total_leakage_kes", ascending=False).head(top_n)

    notes = []
    for _, row in exceptions.iterrows():
        category = row["leakage_category"] + "_kes"
        label = CATEGORY_LABELS.get(category, row["leakage_category"])
        text = (
            f"Loading {row['loading_id']} at {row['depot']} ({row['customer']}, {row['product']}): "
            f"{label} of {_fmt_kes(row['total_leakage_kes'])} detected. "
            f"{CATEGORY_ACTIONS.get(category, 'Route to finance/ops for review.')}"
        )
        notes.append({
            "loading_id": row["loading_id"],
            "depot": row["depot"],
            "customer": row["customer"],
            "leakage_category": row["leakage_category"],
            "total_leakage_kes": float(row["total_leakage_kes"]),
            "narrative": text,
        })
    return notes
