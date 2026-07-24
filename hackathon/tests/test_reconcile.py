import pandas as pd
import pytest

from o2c_pipeline.reconcile import (
    LEAKAGE_CATEGORIES,
    multi_invoice_exceptions,
    overall_summary,
    reconcile,
)

PMS_PRICE = 165.50  # o2c_pipeline.config.DEFAULT_UNIT_PRICE_KES["PMS"]
T0 = pd.Timestamp("2026-06-01 06:00")


@pytest.fixture
def five_scenario_cleaned():
    """One loading per leakage category, plus one fully clean loading, so
    each category's contribution -- and the absence of double counting --
    can be asserted exactly."""
    loadings = pd.DataFrame([
        # L1: clean end-to-end -- should contribute zero leakage
        {"loading_id": "L1", "depot": "Mombasa", "product": "PMS", "customer": "A",
         "volume_loaded_litres": 1000.0, "loading_ts": T0},
        # L2: never dispatched -- dispatch_capture_gap
        {"loading_id": "L2", "depot": "Mombasa", "product": "PMS", "customer": "B",
         "volume_loaded_litres": 1000.0, "loading_ts": T0},
        # L3: dispatched with 5% shrinkage (above the 2% tolerance)
        {"loading_id": "L3", "depot": "Mombasa", "product": "PMS", "customer": "C",
         "volume_loaded_litres": 1000.0, "loading_ts": T0},
        # L4: dispatched in full, never invoiced -- billing_gap
        {"loading_id": "L4", "depot": "Mombasa", "product": "PMS", "customer": "D",
         "volume_loaded_litres": 1000.0, "loading_ts": T0},
        # L5: dispatched in full, invoiced for less (underbilling) and only half paid
        {"loading_id": "L5", "depot": "Mombasa", "product": "PMS", "customer": "E",
         "volume_loaded_litres": 1000.0, "loading_ts": T0},
    ])

    dispatches = pd.DataFrame([
        {"dispatch_id": "D1", "loading_id": "L1", "volume_dispatched_litres": 1000.0,
         "dispatch_ts": T0, "status": "Dispatched"},
        # L2 has no dispatch row at all
        {"dispatch_id": "D3", "loading_id": "L3", "volume_dispatched_litres": 950.0,
         "dispatch_ts": T0, "status": "Dispatched"},
        {"dispatch_id": "D4", "loading_id": "L4", "volume_dispatched_litres": 1000.0,
         "dispatch_ts": T0, "status": "Dispatched"},
        {"dispatch_id": "D5", "loading_id": "L5", "volume_dispatched_litres": 1000.0,
         "dispatch_ts": T0, "status": "Dispatched"},
    ])

    invoices = pd.DataFrame([
        {"invoice_id": "I1", "dispatch_id": "D1", "volume_invoiced_litres": 1000.0,
         "unit_price_kes": PMS_PRICE, "amount_kes": 1000.0 * PMS_PRICE, "invoice_date": T0},
        # D3 (shrinkage case) invoiced correctly for what was actually dispatched
        {"invoice_id": "I3", "dispatch_id": "D3", "volume_invoiced_litres": 950.0,
         "unit_price_kes": PMS_PRICE, "amount_kes": 950.0 * PMS_PRICE, "invoice_date": T0},
        # D4 never invoiced
        {"invoice_id": "I5", "dispatch_id": "D5", "volume_invoiced_litres": 900.0,
         "unit_price_kes": PMS_PRICE, "amount_kes": 900.0 * PMS_PRICE, "invoice_date": T0},
    ])

    payments = pd.DataFrame([
        {"payment_id": "P1", "invoice_id": "I1", "amount_paid_kes": 1000.0 * PMS_PRICE,
         "payment_date": T0},
        {"payment_id": "P3", "invoice_id": "I3", "amount_paid_kes": 950.0 * PMS_PRICE,
         "payment_date": T0},
        {"payment_id": "P5", "invoice_id": "I5", "amount_paid_kes": 900.0 * PMS_PRICE * 0.5,
         "payment_date": T0},
    ])

    return {
        "loading_events": loadings,
        "dispatch_events": dispatches,
        "invoices": invoices,
        "payments": payments,
    }


def test_reconcile_assigns_each_category_to_the_right_loading(five_scenario_cleaned):
    result = reconcile(five_scenario_cleaned).set_index("loading_id")

    assert result.loc["L1", "total_leakage_kes"] == pytest.approx(0.0)

    assert result.loc["L2", "dispatch_capture_gap_kes"] == pytest.approx(1000.0 * PMS_PRICE)
    assert result.loc["L2", "total_leakage_kes"] == pytest.approx(1000.0 * PMS_PRICE)

    assert result.loc["L3", "shrinkage_kes"] == pytest.approx(50.0 * PMS_PRICE)
    assert result.loc["L3", "total_leakage_kes"] == pytest.approx(50.0 * PMS_PRICE)

    assert result.loc["L4", "billing_gap_kes"] == pytest.approx(1000.0 * PMS_PRICE)
    assert result.loc["L4", "total_leakage_kes"] == pytest.approx(1000.0 * PMS_PRICE)

    expected_underbilling = 100.0 * PMS_PRICE
    expected_collections_gap = 900.0 * PMS_PRICE * 0.5
    assert result.loc["L5", "underbilling_kes"] == pytest.approx(expected_underbilling)
    assert result.loc["L5", "collections_gap_kes"] == pytest.approx(expected_collections_gap)
    assert result.loc["L5", "total_leakage_kes"] == pytest.approx(
        expected_underbilling + expected_collections_gap
    )


def test_leakage_categories_sum_to_total_with_no_double_counting(five_scenario_cleaned):
    result = reconcile(five_scenario_cleaned)
    row_sums = result[LEAKAGE_CATEGORIES].sum(axis=1)
    pd.testing.assert_series_equal(row_sums, result["total_leakage_kes"], check_names=False)


def test_cancelled_dispatch_is_never_leakage():
    loadings = pd.DataFrame([
        {"loading_id": "L1", "depot": "Mombasa", "product": "PMS", "customer": "A",
         "volume_loaded_litres": 1000.0, "loading_ts": T0},
    ])
    dispatches = pd.DataFrame([
        {"dispatch_id": "D1", "loading_id": "L1", "volume_dispatched_litres": 100.0,
         "dispatch_ts": T0, "status": "Cancelled"},
    ])
    empty_invoices = pd.DataFrame(columns=["invoice_id", "dispatch_id", "volume_invoiced_litres",
                                            "unit_price_kes", "amount_kes", "invoice_date"])
    empty_payments = pd.DataFrame(columns=["payment_id", "invoice_id", "amount_paid_kes", "payment_date"])

    result = reconcile({
        "loading_events": loadings, "dispatch_events": dispatches,
        "invoices": empty_invoices, "payments": empty_payments,
    })
    assert result.loc[0, "total_leakage_kes"] == 0.0
    assert not result.loc[0, "is_exception"]


def test_overall_summary_matches_row_level_totals(five_scenario_cleaned):
    result = reconcile(five_scenario_cleaned)
    summary = overall_summary(result)
    assert summary["total_leakage_kes"] == pytest.approx(result["total_leakage_kes"].sum())
    assert summary["total_loadings"] == 5
    assert sum(summary["leakage_by_category_kes"].values()) == pytest.approx(summary["total_leakage_kes"])


def test_multi_invoice_exceptions_detects_double_billed_dispatch():
    invoices = pd.DataFrame([
        {"invoice_id": "I1", "dispatch_id": "D1"},
        {"invoice_id": "I2", "dispatch_id": "D1"},
        {"invoice_id": "I3", "dispatch_id": "D2"},
    ])
    flagged = multi_invoice_exceptions({"invoices": invoices})
    assert list(flagged["dispatch_id"]) == ["D1"]
    assert set(flagged.iloc[0]["invoice_ids"]) == {"I1", "I2"}
