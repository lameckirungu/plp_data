"""ROI / business-case calculator.

Turns the reconciliation's annualized leakage figure into a defensible
recovery estimate. Not every leakage category is equally fixable: a
billing-matching gap is closed almost entirely by automation, while
physical shrinkage needs metering/infrastructure investment that this
tool alone can't deliver. The per-category recovery assumptions below
are exactly that -- assumptions -- and are surfaced explicitly rather
than baked silently into one blended number, so a reviewer can push
back on any single one without throwing out the whole estimate.
"""

# Fraction of each category's annualized leakage this tool realistically
# recovers in year one, and why.
RECOVERY_ASSUMPTIONS = {
    "dispatch_capture_gap_kes": {
        "recovery_rate": 0.50,
        "rationale": "Needs gate-capture discipline (automated dispatch confirmation), "
                     "not just software -- partial recovery in year one.",
    },
    "shrinkage_kes": {
        "recovery_rate": 0.40,
        "rationale": "Material transit loss often needs metering/infrastructure fixes "
                     "outside this tool's scope -- flagged for investigation, not "
                     "eliminated by reconciliation alone.",
    },
    "billing_gap_kes": {
        "recovery_rate": 0.85,
        "rationale": "Pure dispatch-to-invoice matching automation -- the highest-confidence "
                     "recovery category.",
    },
    "underbilling_kes": {
        "recovery_rate": 0.85,
        "rationale": "Volume-vs-invoice cross-check is a straightforward automated control.",
    },
    "collections_gap_kes": {
        "recovery_rate": 0.55,
        "rationale": "Automated dunning/aging alerts recover a majority of outstanding AR; "
                     "some customer default is structural and will not close to zero.",
    },
}

# Rough year-one cost to build, integrate, and run this as a hardened,
# monitored service across KPC's depot network (engineering team, cloud
# hosting, ERP/SCADA integration work, and support) -- an explicit,
# adjustable assumption, not a vendor quote.
DEFAULT_IMPLEMENTATION_COST_KES = 75_000_000

# A national multi-depot rollout is phased (pilot depots first, full network
# by Q3-Q4), so year one only captures a fraction of the steady-state annual
# benefit computed below. Steady-state (year two onward, full adoption) is
# reported separately rather than folded in, so the two are never confused.
YEAR1_ADOPTION_RAMP_FACTOR = 0.35

ILLUSTRATIVE_FIGURES_NOTE = (
    "All KES figures are illustrative: they are computed by scaling a 45-day "
    "synthetic simulation (calibrated to plausible KPC depot volumes and ex-depot "
    "pricing, not live operational data) up to an annual run-rate. Treat them as a "
    "directional sizing of the opportunity, and re-run this same pipeline against "
    "real KPC extracts before using any number here in a board-level business case."
)


def compute_roi(summary: dict, implementation_cost_kes: float = DEFAULT_IMPLEMENTATION_COST_KES) -> dict:
    n_days = summary["simulation_window_days"]
    by_category = summary["leakage_by_category_kes"]

    category_breakdown = []
    steady_state_recoverable_annual = 0.0
    for category, amount in by_category.items():
        annualized = amount / n_days * 365
        assumption = RECOVERY_ASSUMPTIONS[category]
        recoverable = annualized * assumption["recovery_rate"]
        steady_state_recoverable_annual += recoverable
        category_breakdown.append({
            "category": category,
            "annualized_leakage_kes": annualized,
            "recovery_rate": assumption["recovery_rate"],
            "recoverable_kes": recoverable,
            "rationale": assumption["rationale"],
        })

    year1_realized_benefit = steady_state_recoverable_annual * YEAR1_ADOPTION_RAMP_FACTOR
    net_benefit_year1 = year1_realized_benefit - implementation_cost_kes
    monthly_recovery_year1 = year1_realized_benefit / 12
    payback_months = (
        implementation_cost_kes / monthly_recovery_year1 if monthly_recovery_year1 > 0 else float("inf")
    )

    return {
        "implementation_cost_kes": implementation_cost_kes,
        "total_annualized_leakage_kes": summary["annualized_leakage_kes"],
        "steady_state_recoverable_annual_kes": steady_state_recoverable_annual,
        "year1_adoption_ramp_factor": YEAR1_ADOPTION_RAMP_FACTOR,
        "year1_realized_benefit_kes": year1_realized_benefit,
        "net_benefit_year1_kes": net_benefit_year1,
        "roi_multiple_year1": year1_realized_benefit / implementation_cost_kes,
        "payback_period_months": round(payback_months, 1),
        "category_breakdown": category_breakdown,
        "note": ILLUSTRATIVE_FIGURES_NOTE,
    }
