"""API tests run against the committed synthetic data (same fixture data
test_pipeline.py exercises) via FastAPI's TestClient -- no server process
needed."""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from o2c_pipeline.pipeline import run_pipeline

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def ensure_pipeline_output():
    """The API reads pipeline output from disk; make sure it exists before
    any test in this module runs."""
    run_pipeline(strict=False)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_kpis_unfiltered():
    resp = client.get("/api/kpis")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_loadings"] > 0
    assert body["total_leakage_kes"] > 0
    category_sum = sum(body["leakage_by_category_kes"].values())
    assert category_sum == pytest.approx(body["total_leakage_kes"], rel=1e-6)


def test_kpis_depot_filter_narrows_results():
    unfiltered = client.get("/api/kpis").json()
    options = client.get("/api/filters/options").json()
    one_depot = options["depots"][0]

    filtered = client.get("/api/kpis", params={"depot": one_depot}).json()
    assert filtered["total_loadings"] < unfiltered["total_loadings"]
    assert all(row["depot"] == one_depot for row in filtered["by_depot"])


def test_kpis_no_matching_rows_returns_404():
    resp = client.get("/api/kpis", params={"customer": "no-such-customer-xyz"})
    assert resp.status_code == 404


def test_filters_options_shape():
    resp = client.get("/api/filters/options")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"depots", "products", "min_date", "max_date"}
    assert len(body["depots"]) > 0


def test_trend_returns_daily_series():
    resp = client.get("/api/trend")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) > 0
    assert set(body[0].keys()) == {"day", "total_leakage_kes"}


def test_exceptions_are_sorted_by_leakage_descending():
    resp = client.get("/api/exceptions", params={"limit": 20})
    assert resp.status_code == 200
    body = resp.json()
    amounts = [row["total_leakage_kes"] for row in body["rows"]]
    assert amounts == sorted(amounts, reverse=True)
    assert all(a > 0 for a in amounts)


def test_exceptions_pagination():
    page1 = client.get("/api/exceptions", params={"limit": 5, "offset": 0}).json()
    page2 = client.get("/api/exceptions", params={"limit": 5, "offset": 5}).json()
    ids1 = {row["loading_id"] for row in page1["rows"]}
    ids2 = {row["loading_id"] for row in page2["rows"]}
    assert ids1.isdisjoint(ids2)


def test_roi_has_expected_fields():
    resp = client.get("/api/roi")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("implementation_cost_kes", "roi_multiple_year1", "payback_period_months"):
        assert key in body


def test_narrative_is_nonempty():
    resp = client.get("/api/narrative")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["executive_narrative"]) > 0


def test_data_quality_gate_passed():
    resp = client.get("/api/data-quality")
    assert resp.status_code == 200
    assert resp.json()["overall_status"] == "PASS"


def test_pipeline_run_endpoint():
    resp = client.post("/api/pipeline/run")
    assert resp.status_code == 200
    assert resp.json()["quality_gate_status"] == "PASS"
