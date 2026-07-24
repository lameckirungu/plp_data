import pandas as pd

from o2c_pipeline.clean import (
    clean_invoices,
    clean_loading_events,
    normalize_depot,
    parse_amount,
    parse_mixed_datetime,
)


def test_parse_mixed_datetime_disambiguates_by_separator():
    series = pd.Series(["2026-06-01 05:47", "01/06/2026 05:47", "31/12/2026 23:59"])
    parsed = parse_mixed_datetime(series)
    assert parsed[0] == pd.Timestamp("2026-06-01 05:47")
    # day/month/year format: 01/06/2026 is 1 June, NOT 6 January
    assert parsed[1] == pd.Timestamp("2026-06-01 05:47")
    assert parsed[2] == pd.Timestamp("2026-12-31 23:59")


def test_parse_mixed_datetime_never_swaps_day_and_month():
    # this is the exact bug class the generator hit: dayfirst ambiguity
    # must never silently reinterpret day-13 (impossible as a month) as a month
    series = pd.Series(["13/06/2026 10:00"])
    parsed = parse_mixed_datetime(series)
    assert parsed[0] == pd.Timestamp("2026-06-13 10:00")


def test_parse_amount_strips_comma_formatting():
    series = pd.Series(["4,246,867.69", "165.50", None])
    parsed = parse_amount(series)
    assert parsed[0] == 4246867.69
    assert parsed[1] == 165.50
    assert pd.isna(parsed[2])


def test_normalize_depot_maps_known_aliases():
    series = pd.Series(["MOMBASA", "Nairobi Depot", "nrb", " Kisii ", "unknown place"])
    normalized = normalize_depot(series)
    assert list(normalized[:4]) == ["Mombasa", "Nairobi", "Nairobi", "Kisii"]
    assert pd.isna(normalized[4])


def _loading_row(**overrides):
    row = {
        "loading_id": "LD000001",
        "depot": "Mombasa",
        "product": "PMS",
        "customer": "Acme Fuels",
        "truck_id": "TRK-100",
        "volume_loaded_litres": "1000",
        "meter_start": "1000000.0",
        "meter_end": "1001000.0",
        "loading_ts": "2026-06-01 05:47",
    }
    row.update(overrides)
    return row


def test_clean_loading_events_drops_non_positive_volume_and_fills_missing_customer():
    raw = pd.DataFrame([
        _loading_row(loading_id="LD1", customer=None),
        _loading_row(loading_id="LD2", volume_loaded_litres="0"),
        _loading_row(loading_id="LD3", volume_loaded_litres="-500"),
        _loading_row(loading_id="LD4"),
    ])
    cleaned, issues = clean_loading_events(raw)

    assert set(cleaned["loading_id"]) == {"LD1", "LD4"}
    assert cleaned.loc[cleaned["loading_id"] == "LD1", "customer"].iloc[0] == "UNKNOWN CUSTOMER"
    assert any(i["check"] == "non_positive_volume" and i["count"] == 2 for i in issues)
    assert any(i["check"] == "missing_customer" for i in issues)
    assert cleaned["volume_loaded_litres"].dtype == float


def _invoice_row(**overrides):
    row = {
        "invoice_id": "INV1",
        "dispatch_id": "DS1",
        "customer": "Acme Fuels",
        "product": "PMS",
        "volume_invoiced_litres": "1000",
        "unit_price_kes": "165.50",
        "amount_kes": "165500.00",
        "invoice_date": "2026-06-02 10:00",
        "currency": "KES",
    }
    row.update(overrides)
    return row


def test_clean_invoices_backfills_missing_unit_price_from_amount_and_volume():
    raw = pd.DataFrame([_invoice_row(invoice_id="INV1", unit_price_kes=None)])
    cleaned, issues = clean_invoices(raw)

    assert cleaned.loc[0, "unit_price_kes"] == 165.50
    assert any(i["check"] == "missing_unit_price_backfilled" for i in issues)


def test_clean_invoices_flags_dispatch_billed_on_multiple_invoices():
    raw = pd.DataFrame([
        _invoice_row(invoice_id="INV1", dispatch_id="DS1"),
        _invoice_row(invoice_id="INV2", dispatch_id="DS1"),
        _invoice_row(invoice_id="INV3", dispatch_id="DS2"),
    ])
    _, issues = clean_invoices(raw)

    dupe_issue = next(i for i in issues if i["check"] == "dispatch_with_multiple_invoices")
    assert dupe_issue["count"] == 2  # both INV1 and INV2 rows are implicated
