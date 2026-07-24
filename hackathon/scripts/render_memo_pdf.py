#!/usr/bin/env python3
"""Render the one-page problem-framing memo to PDF, matching the business-
memo deliverable format used in prior weeks of this fellowship.

Run: python scripts/render_memo_pdf.py
"""

import json

from fpdf import FPDF, XPos, YPos

from o2c_pipeline.config import LEAKAGE_SUMMARY_JSON, REPORTS_DIR

INK = (11, 11, 11)
SECONDARY = (82, 81, 78)
ACCENT = (42, 120, 214)
GRIDLINE = (225, 224, 217)

CATEGORY_ROWS = [
    ("Dispatch capture gap", "Loaded, but no dispatch record exists at all"),
    ("Shrinkage", "Dispatched volume is materially below loaded volume"),
    ("Billing gap", "Confirmed dispatch, but never invoiced"),
    ("Underbilling", "Invoiced for less volume than was dispatched"),
    ("Collections gap", "Invoiced correctly, but payment is partial or outstanding"),
]


def fmt_kes(value: float) -> str:
    if abs(value) >= 1e9:
        return f"KES {value / 1e9:,.2f}B"
    return f"KES {value / 1e6:,.1f}M"


class MemoPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(*INK)
        self.cell(0, 8, "KPC Order-to-Cash Leakage - Problem-Framing Memo",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*SECONDARY)
        self.cell(0, 5, "Inuka Hackathon - Stage 1 (Data Engineering) - Problem 7D, Domain D: "
                         "Revenue Assurance, Billing & Reconciliation", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(0, 5, "Author: Lameck Irungu  |  Date: 24 July 2026", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*GRIDLINE)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(6)

    def section(self, title: str):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*ACCENT)
        self.cell(0, 7, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*INK)

    def body(self, text: str):
        self.set_font("Helvetica", "", 9.5)
        self.multi_cell(0, 4.6, text)
        self.ln(1)


def build_pdf(summary: dict) -> MemoPDF:
    top_depot = max(summary["by_depot"], key=lambda r: r["total_leakage_kes"])
    top_customer = max(summary["by_customer"], key=lambda r: r["total_leakage_kes"])

    pdf = MemoPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    pdf.section("The problem")
    pdf.body(
        "KPC's order-to-cash cycle runs through four handoffs -- depot loading, gate "
        "dispatch, finance invoicing, and AR payment -- each owned by a different system "
        "and, today, reconciled manually if at all. Every handoff is a place product or "
        "revenue can go missing without anyone noticing until a periodic audit, weeks "
        "later, tries to explain a gap."
    )

    pdf.section("Why it matters now")
    pdf.body(
        "This is a revenue-assurance problem, not a data-quality nicety. Reconciliation "
        "gaps compound in two directions: lost cash (shipped and never billed, or billed "
        "and never collected) and lost audit trail (KPC cannot show a regulator or lender "
        "exactly where a shilling of expected revenue went). Closing it needs the same "
        "discipline telecom and utility revenue-assurance teams apply: automated, "
        "continuous matching across every handoff, not a spot-check."
    )

    pdf.section("What we built (Stage 1 scope)")
    pdf.body(
        "An automated ETL + reconciliation pipeline that ingests four messy, independently-"
        "owned exports (mixed date formats, currency-formatted numbers, depot-name aliasing, "
        "missing fields); cleans and validates every table against explicit schemas with a "
        "data-quality gate that fails hard on structural defects but never on the business "
        "gaps the pipeline exists to find; and reconciles the full loading -> dispatch -> "
        "invoice -> payment chain, attributing every leaked shilling to exactly one of five "
        "named categories so nothing is double-counted:"
    )

    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(245, 245, 243)
    pdf.cell(48, 6, "Category", border=0, fill=True)
    pdf.cell(0, 6, "What it means", border=0, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    for name, desc in CATEGORY_ROWS:
        pdf.cell(48, 5.5, name)
        pdf.cell(0, 5.5, desc, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    pdf.body(
        "It ships evidence, not just code: 19 automated tests (unit + integration), a CI "
        "workflow that lints, tests, and re-runs the quality gate on every push, and a "
        "containerized executive dashboard with AI-generated audit narratives and an ROI model."
    )

    pdf.section("Early findings")
    pdf.body(
        f"Run against a synthetic dataset calibrated to plausible KPC depot volumes and "
        f"ex-depot pricing (45 days, 6 depots, 3 products, 20 customers -- not live KPC "
        f"data): {summary['leakage_pct_of_expected_revenue']:.1f}% of expected ex-depot "
        f"revenue leaks before it becomes collected cash -- {fmt_kes(summary['total_leakage_kes'])} "
        f"over the window, ~{fmt_kes(summary['annualized_leakage_kes'])} annualized. "
        f"{summary['exception_rate_pct']:.1f}% of loadings ({summary['exception_count']} of "
        f"{summary['total_loadings']}) carry at least one reconciliation exception. Leakage "
        f"concentrates: {top_depot['depot']} depot and {top_customer['customer']} are the "
        f"single largest depot- and customer-level exposures respectively -- a few targeted "
        f"fixes close most of the gap, not a company-wide program."
    )

    pdf.section("What's next")
    pdf.body(
        "Stage 2: connect to live KPC extracts; add statistical diagnostics and a predictive "
        "shrinkage/collections-risk model on top of this reconciliation foundation. Stage 3: "
        "harden into the monitored, CI/CD-deployed service this pipeline already points at, "
        "and validate the ROI model's assumptions against real recovery data."
    )

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*SECONDARY)
    pdf.multi_cell(
        0, 4,
        "All KES figures in this memo and the dashboard are illustrative -- computed on "
        "synthetic data, not KPC's live systems. Every claim above is reproducible: "
        "`make pipeline` regenerates every number from the committed source data.",
    )
    return pdf


def main():
    with open(LEAKAGE_SUMMARY_JSON) as f:
        summary = json.load(f)
    pdf = build_pdf(summary)
    out_path = REPORTS_DIR / "Inuka_Stage1_Memo_Lameck.pdf"
    pdf.output(str(out_path))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
