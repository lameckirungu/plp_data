#!/usr/bin/env python3
"""Render the 5-minute Stage 1 pitch deck to PDF.

Widescreen (16:9) slides, built from the pipeline's own current output --
regenerate after `make pipeline` to keep every number on the deck honest.

Run: python scripts/render_pitch_deck.py
"""

import json

from fpdf import FPDF
from PIL import Image

from o2c_pipeline.config import LEAKAGE_CHART_PNG, LEAKAGE_SUMMARY_JSON, REPORTS_DIR

# 16:9 widescreen, matching standard slide dimensions (mm).
PAGE_W, PAGE_H = 338, 190

INK = (11, 11, 11)
SECONDARY = (82, 81, 78)
MUTED = (137, 135, 129)
ACCENT = (42, 120, 214)
GOOD = (12, 163, 12)
CRITICAL = (208, 59, 59)
GRIDLINE = (225, 224, 217)
SURFACE = (252, 252, 251)

SCREENSHOTS = REPORTS_DIR / "screenshots"


def fmt_kes(value: float) -> str:
    if abs(value) >= 1e9:
        return f"KES {value / 1e9:,.2f}B"
    return f"KES {value / 1e6:,.1f}M"


def top_panels_crop(chart_path) -> Image.Image:
    """The 4-panel report chart's own suptitle duplicates the slide title,
    and all 4 panels together don't fit a slide -- crop to just the top
    row (category + depot breakdowns), which carries the headline story."""
    img = Image.open(chart_path)
    w, h = img.size
    return img.crop((0, int(h * 0.10), w, int(h * 0.50)))


def crop_top(image_path, fraction: float) -> Image.Image:
    """Crop a screenshot to its top `fraction` -- used to fit a full-page
    dashboard capture into the vertical space a slide actually has."""
    img = Image.open(image_path)
    w, h = img.size
    return img.crop((0, 0, w, int(h * fraction)))


class Deck(FPDF):
    def __init__(self):
        # format=(338, 190) already IS the landscape shape (w > h) --
        # orientation="L" would swap it back to portrait, so leave the
        # default portrait orientation and let the tuple speak for itself.
        super().__init__(unit="mm", format=(PAGE_W, PAGE_H))
        self.set_auto_page_break(False)

    def slide(self, kicker: str = "", number: str = ""):
        self.add_page()
        self.set_fill_color(*SURFACE)
        self.rect(0, 0, PAGE_W, PAGE_H, "F")
        if kicker:
            self.set_xy(18, 14)
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*ACCENT)
            self.cell(0, 6, kicker.upper())
        if number:
            self.set_xy(0, PAGE_H - 14)
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*MUTED)
            self.cell(PAGE_W - 14, 6, number, align="R")

    def slide_title(self, text: str, y: float = 24, size: int = 30):
        self.set_xy(18, y)
        self.set_font("Helvetica", "B", size)
        self.set_text_color(*INK)
        self.multi_cell(PAGE_W - 36, size * 0.42, text)

    def body(self, text: str, x: float, y: float, w: float, size: int = 13, color=SECONDARY):
        self.set_xy(x, y)
        self.set_font("Helvetica", "", size)
        self.set_text_color(*color)
        self.multi_cell(w, size * 0.52, text)

    def bullets(self, items: list[str], x: float, y: float, w: float, size: int = 13, gap: float = 4):
        self.set_font("Helvetica", "", size)
        self.set_text_color(*SECONDARY)
        cy = y
        for item in items:
            self.set_xy(x, cy)
            self.set_text_color(*ACCENT)
            self.cell(6, size * 0.52, "-")
            self.set_xy(x + 7, cy)
            self.set_text_color(*SECONDARY)
            self.multi_cell(w - 7, size * 0.52, item)
            cy = self.get_y() + gap

    def stat(self, x: float, y: float, w: float, label: str, value: str, color=INK):
        self.set_xy(x, y)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*MUTED)
        self.cell(w, 5, label.upper())
        self.set_xy(x, y + 6)
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(*color)
        self.cell(w, 10, value)

    def note(self, text: str):
        self.set_xy(18, PAGE_H - 14)
        self.set_font("Helvetica", "I", 8.5)
        self.set_text_color(*MUTED)
        self.cell(PAGE_W - 36, 5, text)


def build_deck(summary: dict) -> Deck:
    pdf = Deck()

    # 1. Title
    pdf.slide()
    pdf.set_xy(18, 60)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 8, "INUKA HACKATHON -- STAGE 1: DATA ENGINEERING -- PROBLEM 7D")
    pdf.set_xy(18, 76)
    pdf.set_font("Helvetica", "B", 40)
    pdf.set_text_color(*INK)
    pdf.multi_cell(PAGE_W - 36, 17, "Closing KPC's Order-to-Cash\nLeakage Gap")
    pdf.set_xy(18, 132)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(*SECONDARY)
    pdf.cell(0, 7, "Reconciling loading, dispatch, invoicing, and payment -- automatically, with evidence.")
    pdf.set_xy(18, PAGE_H - 22)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 6, "Lameck Irungu  |  24 July 2026")

    # 2. The problem
    pdf.slide(kicker="The problem", number="1 / 7")
    pdf.slide_title("Revenue leaks at every handoff --\nand nobody finds out until the audit.")
    pdf.bullets(
        [
            "KPC's order-to-cash cycle runs through 4 handoffs: depot loading, gate "
            "dispatch, finance invoicing, AR payment -- each owned by a different system.",
            "Today, reconciling them is manual, periodic, or doesn't happen at all.",
            "Every handoff is a place product or revenue can go missing -- with zero "
            "visibility until a month-end audit tries to explain the gap.",
            "This isn't a data-quality nicety. It's lost cash AND a lost audit trail: "
            "KPC can't show a regulator or lender where a shilling of revenue went.",
        ],
        x=18, y=70, w=PAGE_W - 36, size=14, gap=7,
    )

    # 3. The approach
    pdf.slide(kicker="What we built", number="2 / 7")
    pdf.slide_title("An automated pipeline -- not a spreadsheet audit.")
    pdf.bullets(
        [
            "Ingest 4 messy, independently-owned exports (mixed date formats, "
            "currency-formatted numbers, depot-name aliasing, missing fields).",
            "Clean + validate against explicit schemas, with a data-quality gate that "
            "fails hard on structural defects -- but never on the business gaps we "
            "exist to measure.",
            "Reconcile the full loading -> dispatch -> invoice -> payment chain, "
            "attributing every leaked shilling to exactly one of 5 categories.",
            "Ship it as a real product: a FastAPI backend + React dashboard, "
            "containerized, with CI that lints, tests, and re-runs the quality gate "
            "on every push.",
        ],
        x=18, y=70, w=PAGE_W - 36, size=14, gap=6.5,
    )

    # 4. The taxonomy
    pdf.slide(kicker="The taxonomy", number="3 / 7")
    pdf.slide_title("Five categories. Mutually exclusive. Zero double-counting.")
    rows = [
        ("Dispatch capture gap", "Loaded, but no dispatch record exists at all"),
        ("Shrinkage", "Dispatched volume is materially below loaded volume"),
        ("Billing gap", "Confirmed dispatch, but never invoiced"),
        ("Underbilling", "Invoiced for less volume than was dispatched"),
        ("Collections gap", "Invoiced correctly, but payment is partial or outstanding"),
    ]
    cy = 74
    for name, desc in rows:
        pdf.set_xy(18, cy)
        pdf.set_font("Helvetica", "B", 15)
        pdf.set_text_color(*ACCENT)
        pdf.cell(90, 8, name)
        pdf.set_xy(112, cy)
        pdf.set_font("Helvetica", "", 14)
        pdf.set_text_color(*SECONDARY)
        pdf.cell(0, 8, desc)
        cy += 16

    # 5. Evidence
    pdf.slide(kicker="Evidence", number="4 / 7")
    pdf.slide_title(
        f"{summary['leakage_pct_of_expected_revenue']:.1f}% of expected revenue "
        f"never converts to cash.",
        size=26,
    )
    leakage_pct = f"{summary['leakage_pct_of_expected_revenue']:.1f}%"
    exceptions = f"{summary['exception_count']:,} / {summary['total_loadings']:,}"
    pdf.stat(18, 62, 70, "Total leakage (45 days)", fmt_kes(summary["total_leakage_kes"]), color=CRITICAL)
    pdf.stat(94, 62, 70, "% of expected revenue", leakage_pct, color=CRITICAL)
    pdf.stat(170, 62, 70, "Annualized", fmt_kes(summary["annualized_leakage_kes"]))
    pdf.stat(246, 62, 80, "Exceptions flagged", exceptions)
    if LEAKAGE_CHART_PNG.exists():
        pdf.image(top_panels_crop(LEAKAGE_CHART_PNG), x=34, y=96, w=270)
    pdf.note("Synthetic dataset calibrated to plausible KPC depot volumes -- illustrative, not live data.")

    # 6. The product
    pdf.slide(kicker="The product", number="5 / 7")
    pdf.slide_title("A real dashboard -- live filters, audit trail, ROI.", size=26)
    overview_shot = SCREENSHOTS / "dashboard_overview.jpg"
    if overview_shot.exists():
        pdf.image(crop_top(overview_shot, 0.73), x=64, y=58, w=210)
    pdf.note("React + TypeScript + Recharts. Filters call the API live -- not a static export.")

    # 7. Impact / ROI
    roi = summary.get("roi", {})
    pdf.slide(kicker="Impact", number="6 / 7")
    pdf.slide_title("Targeted fixes close most of the gap.", size=26)
    if roi:
        benefit = fmt_kes(roi["year1_realized_benefit_kes"])
        pdf.stat(18, 62, 70, "Year-1 build cost", fmt_kes(roi["implementation_cost_kes"]))
        pdf.stat(94, 62, 70, "Year-1 realized benefit", benefit, color=GOOD)
        pdf.stat(170, 62, 70, "Payback period", f"{roi['payback_period_months']:.1f} months")
        pdf.stat(246, 62, 80, "Year-1 ROI multiple", f"{roi['roi_multiple_year1']:.1f}x", color=ACCENT)
    top_depot = max(summary["by_depot"], key=lambda r: r["total_leakage_kes"])
    top_customer = max(summary["by_customer"], key=lambda r: r["total_leakage_kes"])
    pdf.body(
        f"{top_depot['depot']} depot and {top_customer['customer']} are the single largest "
        f"depot- and customer-level exposures. Leakage concentrates -- a few targeted "
        f"interventions, not a company-wide program, close most of the gap.",
        x=18, y=100, w=PAGE_W - 36, size=14,
    )
    pdf.note("Illustrative figures, scaled from a 45-day simulation -- re-validate against live data.")

    # 8. Close / roadmap
    pdf.slide(kicker="What's next", number="7 / 7")
    pdf.slide_title("Stage 1 is the foundation. Stage 2 builds intelligence on it.")
    pdf.bullets(
        [
            "Stage 2: connect to live KPC extracts; statistical diagnostics and a "
            "predictive shrinkage/collections-risk model on top of this reconciliation.",
            "Stage 3: harden into the monitored, CI/CD-deployed service this repo "
            "already points at; validate the ROI model against real recovery data.",
            "The ask: KPC operational data access to replace the synthetic dataset "
            "and turn this from a directional estimate into a validated business case.",
        ],
        x=18, y=70, w=PAGE_W - 36, size=14, gap=7,
    )
    pdf.set_xy(18, PAGE_H - 30)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 7, "Thank you -- questions?")

    return pdf


def main():
    with open(LEAKAGE_SUMMARY_JSON) as f:
        summary = json.load(f)
    pdf = build_deck(summary)
    out_path = REPORTS_DIR / "Inuka_Stage1_Pitch_Lameck.pdf"
    pdf.output(str(out_path))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
