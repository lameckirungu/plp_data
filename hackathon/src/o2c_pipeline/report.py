"""Static chart generation for the reconciliation report.

Colors follow the validated palette in the dataviz skill (categorical hues
assigned by category identity, fixed order, never re-cycled by sort rank).
Bars carry direct value labels specifically because three of these five
hues sit below 3:1 contrast against a light surface -- the palette's own
"relief rule" for that case is visible labels, which this chart ships.
"""

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")

from o2c_pipeline.config import LEAKAGE_CHART_PNG
from o2c_pipeline.reconcile import LEAKAGE_CATEGORIES

CATEGORY_LABELS = {
    "dispatch_capture_gap_kes": "Dispatch capture gap",
    "shrinkage_kes": "Shrinkage",
    "billing_gap_kes": "Billing gap",
    "underbilling_kes": "Underbilling",
    "collections_gap_kes": "Collections gap",
}
CATEGORY_COLORS = {
    "dispatch_capture_gap_kes": "#2a78d6",  # slot 1 blue
    "shrinkage_kes": "#eb6834",             # slot 2 orange
    "billing_gap_kes": "#1baf7a",           # slot 3 aqua
    "underbilling_kes": "#eda100",          # slot 4 yellow
    "collections_gap_kes": "#e87ba4",       # slot 5 magenta
}
MAGNITUDE_BLUE = "#2a78d6"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
SURFACE = "#fcfcfb"


def _style_axis(ax):
    ax.set_facecolor(SURFACE)
    ax.grid(axis="x", color=GRIDLINE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(INK_MUTED)
    ax.tick_params(colors=INK_SECONDARY, labelsize=9)


def _fmt_millions(value: float) -> str:
    return f"KES {value / 1e6:,.1f}M"


def _labeled_hbar(ax, labels, values, colors, title: str, xlim_pad: float = 1.25) -> None:
    bars = ax.barh(labels, values, color=colors, height=0.6, zorder=3)
    max_val = max(values)
    for bar, v in zip(bars, values):
        ax.text(
            bar.get_width() + max_val * 0.02, bar.get_y() + bar.get_height() / 2,
            _fmt_millions(v), va="center", fontsize=9, color=INK_PRIMARY,
        )
    ax.set_xlim(0, max_val * xlim_pad)
    ax.set_title(title, fontsize=11, color=INK_PRIMARY, loc="left", fontweight="bold")
    _style_axis(ax)
    ax.set_xticklabels([])


def generate_leakage_chart(reconciled: pd.DataFrame, summary: dict, out_path=None) -> None:
    out_path = out_path or LEAKAGE_CHART_PNG
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), facecolor=SURFACE)
    fig.suptitle(
        "KPC Order-to-Cash Leakage — Reconciliation Findings",
        fontsize=15, fontweight="bold", color=INK_PRIMARY, x=0.02, ha="left",
    )
    fig.text(
        0.02, 0.945,
        f"Simulation window: {summary['simulation_window_days']} days   |   "
        f"Total leakage: {_fmt_millions(summary['total_leakage_kes'])} "
        f"({summary['leakage_pct_of_expected_revenue']:.1f}% of expected revenue)",
        fontsize=10, color=INK_SECONDARY,
    )

    # Panel A: leakage by category -- categorical identity, fixed hue per category
    ax = axes[0, 0]
    by_cat = summary["leakage_by_category_kes"]
    cats = LEAKAGE_CATEGORIES
    values = [by_cat[c] for c in cats]
    order = np.argsort(values)  # sort by magnitude for readability; color stays tied to category
    labels = [CATEGORY_LABELS[cats[i]] for i in order]
    colors = [CATEGORY_COLORS[cats[i]] for i in order]
    vals = [values[i] for i in order]
    _labeled_hbar(ax, labels, vals, colors, "Leakage by category")

    # Panel B: leakage by depot -- single measure, magnitude hue
    ax = axes[0, 1]
    by_depot = pd.DataFrame(summary["by_depot"]).sort_values("total_leakage_kes", ascending=True)
    _labeled_hbar(
        ax, by_depot["depot"], by_depot["total_leakage_kes"].tolist(),
        MAGNITUDE_BLUE, "Leakage by depot",
    )

    # Panel C: daily leakage trend -- single measure over time
    ax = axes[1, 0]
    daily = (
        reconciled.dropna(subset=["loading_ts"])
        .assign(day=reconciled["loading_ts"].dt.date)
        .groupby("day")["total_leakage_kes"].sum()
    )
    ax.plot(list(daily.index), daily.values, color=MAGNITUDE_BLUE, linewidth=2, zorder=3)
    ax.fill_between(list(daily.index), daily.values, color=MAGNITUDE_BLUE, alpha=0.12, zorder=2)
    ax.set_title("Daily leakage trend", fontsize=11, color=INK_PRIMARY, loc="left", fontweight="bold")
    _style_axis(ax)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v/1e6:.1f}M")
    fig.autofmt_xdate(rotation=30)

    # Panel D: top customers by leakage exposure -- same magnitude hue as panel B
    ax = axes[1, 1]
    by_cust = (
        pd.DataFrame(summary["by_customer"])
        .sort_values("total_leakage_kes", ascending=True)
        .tail(8)
    )
    _labeled_hbar(
        ax, by_cust["customer"], by_cust["total_leakage_kes"].tolist(),
        MAGNITUDE_BLUE, "Top customers by leakage exposure", xlim_pad=1.3,
    )

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(out_path, dpi=160, facecolor=SURFACE)
    plt.close(fig)
