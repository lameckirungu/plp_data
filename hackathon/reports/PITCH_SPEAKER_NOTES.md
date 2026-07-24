# Stage 1 Pitch — Speaker Notes (5:00 target)

Deck: `Inuka_Stage1_Pitch_Lameck.pdf` (8 slides, 16:9). Regenerate with
`python scripts/render_pitch_deck.py` after any `make pipeline` run so every number
stays live.

| # | Slide | Time | Say |
|---|---|---|---|
| 1 | Title | 0:15 | "KPC's order-to-cash cycle leaks revenue at every handoff, and today nobody finds out until the audit. This is how we close that gap." |
| 2 | The problem | 0:45 | Name the 4 handoffs, each owned by a different system. Land the line: "it's not a data-quality nicety — it's lost cash *and* a lost audit trail." |
| 3 | What we built | 0:45 | Walk the pipeline once, fast: ingest → clean → quality gate → reconcile. Emphasize the gate never fails on business gaps — that's the point of the tool. |
| 4 | The taxonomy | 0:30 | Read the 5 categories quickly — this is the "aha": every shilling of leakage has exactly one home, nothing double-counted. |
| 5 | Evidence | 1:00 | Hit the headline number hard: **5.5% of expected revenue, ~KES 5.6B annualized**. Point at the chart — collections gap and dispatch capture gap dominate. Say "illustrative, synthetic data" out loud — don't let a judge catch it first. |
| 6 | The product | 0:45 | **If time allows, tab over to the live dashboard here** instead of the screenshot — filter by one depot live, show the number move. This is the differentiator: a real web app, not a notebook. |
| 7 | Impact | 0:45 | Read the 4 numbers left to right. Land on: "targeted intervention, not a company-wide program, closes most of the gap." |
| 8 | What's next | 0:15 | One line on Stage 2/3, then the ask: KPC data access to validate this against reality. |

## If asked in Q&A

- **"Is this real KPC data?"** No — synthetic, calibrated to plausible depot volumes
  and ex-depot pricing. Every figure is reproducible from committed source data via
  `make pipeline`; the pipeline is what's real, not the numbers yet.
- **"Why these five categories and not more?"** They're mutually exclusive by
  construction — every loading is valued once, then debited across exactly one
  category, so totals never double-count. See `reconcile.py`.
- **"What happens if the data is bad?"** The quality gate hard-fails on structural
  defects (bad dtypes, orphan foreign keys, malformed dates) before reconciliation
  ever runs — see the Data Quality tab.
- **"Why not just use Excel?"** 2,826 loadings across 6 depots, 4 disconnected
  source systems, reconciled in ~2 seconds with a full audit trail. That doesn't
  scale as a manual process, which is exactly why it isn't being done today.
