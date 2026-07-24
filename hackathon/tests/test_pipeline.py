import pandas as pd
import pytest

from o2c_pipeline.config import (
    DQ_ISSUES_LOG,
    LEAKAGE_CHART_PNG,
    LEAKAGE_SUMMARY_JSON,
    RECONCILED_OUTPUT,
)
from o2c_pipeline.pipeline import run_pipeline
from o2c_pipeline.reconcile import LEAKAGE_CATEGORIES


def test_pipeline_runs_end_to_end_and_passes_its_own_quality_gate():
    """Integration test against the committed synthetic raw data in
    data/raw/ -- this is the same command CI and `make pipeline` run."""
    summary = run_pipeline(strict=True)

    assert summary["data_quality"]["overall_status"] == "PASS"
    assert summary["total_loadings"] > 0
    assert summary["total_leakage_kes"] > 0
    assert 0 < summary["leakage_pct_of_expected_revenue"] < 100

    category_sum = sum(summary["leakage_by_category_kes"].values())
    assert category_sum == pytest.approx(summary["total_leakage_kes"], rel=1e-6)

    assert RECONCILED_OUTPUT.exists()
    assert LEAKAGE_SUMMARY_JSON.exists()
    assert LEAKAGE_CHART_PNG.exists()
    assert DQ_ISSUES_LOG.exists()


def test_reconciled_output_has_no_orphaned_leakage_amounts():
    run_pipeline(strict=True)
    reconciled = pd.read_csv(RECONCILED_OUTPUT)
    row_sums = reconciled[LEAKAGE_CATEGORIES].sum(axis=1)
    assert (row_sums - reconciled["total_leakage_kes"]).abs().max() < 1e-6
