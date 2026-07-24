import pandas as pd

from o2c_pipeline.quality import (
    check_issue_thresholds,
    check_referential_integrity,
    run_quality_gate,
)

T0 = pd.Timestamp("2026-06-01 06:00")


def _valid_cleaned():
    loadings = pd.DataFrame([
        {"loading_id": "L1", "depot": "Mombasa", "product": "PMS", "customer": "A",
         "volume_loaded_litres": 1000.0, "loading_ts": T0},
        {"loading_id": "L2", "depot": "Nairobi", "product": "AGO", "customer": "B",
         "volume_loaded_litres": 2000.0, "loading_ts": T0},
    ])
    dispatches = pd.DataFrame([
        {"dispatch_id": "D1", "loading_id": "L1", "volume_dispatched_litres": 1000.0,
         "dispatch_ts": T0, "status": "Dispatched"},
        {"dispatch_id": "D2", "loading_id": "L2", "volume_dispatched_litres": 2000.0,
         "dispatch_ts": T0, "status": "Dispatched"},
    ])
    invoices = pd.DataFrame([
        {"invoice_id": "I1", "dispatch_id": "D1", "volume_invoiced_litres": 1000.0,
         "unit_price_kes": 165.50, "amount_kes": 165500.0, "invoice_date": T0},
    ])
    payments = pd.DataFrame([
        {"payment_id": "P1", "invoice_id": "I1", "amount_paid_kes": 165500.0, "payment_date": T0},
    ])
    return {
        "loading_events": loadings, "dispatch_events": dispatches,
        "invoices": invoices, "payments": payments,
    }


def test_quality_gate_passes_on_well_formed_data():
    cleaned = _valid_cleaned()
    empty_issues = pd.DataFrame(columns=["table", "check", "severity", "count", "detail"])
    report = run_quality_gate(cleaned, empty_issues)
    assert report.overall_status == "PASS"


def test_referential_integrity_fails_on_orphan_foreign_key():
    cleaned = _valid_cleaned()
    # dispatch D2 now points at a loading_id that does not exist
    cleaned["dispatch_events"].loc[1, "loading_id"] = "GHOST_LOADING"
    results = check_referential_integrity(cleaned)
    dispatch_check = next(r for r in results if r.name == "referential_integrity:dispatch_to_loading")
    assert dispatch_check.status == "FAIL"


def test_referential_integrity_passes_when_all_fks_resolve():
    cleaned = _valid_cleaned()
    results = check_referential_integrity(cleaned)
    assert all(r.status == "PASS" for r in results)


def test_critical_issue_above_threshold_fails_gate():
    cleaned = _valid_cleaned()
    # 1 bad row out of 2 is 50% -- far past the 1% critical-issue tolerance
    issues = pd.DataFrame([
        {"table": "loading_events", "check": "non_positive_volume", "severity": "critical",
         "count": 1, "detail": ""},
    ])
    results = check_issue_thresholds(issues, cleaned)
    assert results[0].status == "FAIL"


def test_warning_severity_never_fails_the_gate():
    cleaned = _valid_cleaned()
    empty_issues = pd.DataFrame(columns=["table", "check", "severity", "count", "detail"])
    # a business gap (missing invoice) is not represented in issues_df at all,
    # and a "warning"-severity clean.py issue must not affect gate status either
    warning_issues = pd.DataFrame([
        {"table": "loading_events", "check": "missing_customer", "severity": "warning",
         "count": 2, "detail": ""},
    ])
    report_empty = run_quality_gate(cleaned, empty_issues)
    report_warning = run_quality_gate(cleaned, warning_issues)
    assert report_empty.overall_status == "PASS"
    assert report_warning.overall_status == "PASS"
