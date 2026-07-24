"""Data-quality gates: schema validation, referential integrity, and a
pass/fail decision the pipeline enforces before reconciliation runs.

Two different things get checked here, and it matters that they stay
separate:

  * STRUCTURAL problems (wrong dtype, malformed dates, negative volumes,
    orphan foreign keys, duplicate primary keys) are genuine defects --
    the gate fails hard if they exceed a small tolerance.
  * BUSINESS gaps (a dispatch with no invoice, an invoice with no
    payment) are exactly the phenomenon this pipeline exists to measure.
    They are never a gate failure; they are reconciliation's job
    (reconcile.py), not a data-quality defect.
"""

from dataclasses import dataclass, field

import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema

CRITICAL_ISSUE_MAX_PCT = 1.0   # a "critical" clean.py issue may affect at most this % of rows
ORPHAN_FK_MAX_PCT = 0.1        # a child row referencing a non-existent parent is a hard defect

LOADING_EVENTS_SCHEMA = DataFrameSchema(
    {
        "loading_id": Column(str, unique=True, nullable=False),
        "depot": Column(str, nullable=True),
        "product": Column(str, Check.isin(["PMS", "AGO", "IK"]), nullable=False),
        "customer": Column(str, nullable=False),
        "volume_loaded_litres": Column(float, Check.gt(0), nullable=False),
        "loading_ts": Column("datetime64[ns]", nullable=True),
    },
    strict=False,
    coerce=False,
)

DISPATCH_EVENTS_SCHEMA = DataFrameSchema(
    {
        "dispatch_id": Column(str, unique=True, nullable=False),
        "loading_id": Column(str, nullable=False),
        "volume_dispatched_litres": Column(float, Check.gt(0), nullable=False),
        "dispatch_ts": Column("datetime64[ns]", nullable=True),
        "status": Column(str, Check.isin(["Dispatched", "Cancelled"]), nullable=False),
    },
    strict=False,
    coerce=False,
)

INVOICES_SCHEMA = DataFrameSchema(
    {
        "invoice_id": Column(str, unique=True, nullable=False),
        "dispatch_id": Column(str, nullable=False),
        "volume_invoiced_litres": Column(float, Check.gt(0), nullable=False),
        "unit_price_kes": Column(float, Check.gt(0), nullable=False),
        "amount_kes": Column(float, Check.gt(0), nullable=False),
        "invoice_date": Column("datetime64[ns]", nullable=True),
    },
    strict=False,
    coerce=False,
)

PAYMENTS_SCHEMA = DataFrameSchema(
    {
        "payment_id": Column(str, unique=True, nullable=False),
        "invoice_id": Column(str, nullable=False),
        "amount_paid_kes": Column(float, Check.gt(0), nullable=False),
        "payment_date": Column("datetime64[ns]", nullable=True),
    },
    strict=False,
    coerce=False,
)

SCHEMAS = {
    "loading_events": LOADING_EVENTS_SCHEMA,
    "dispatch_events": DISPATCH_EVENTS_SCHEMA,
    "invoices": INVOICES_SCHEMA,
    "payments": PAYMENTS_SCHEMA,
}


@dataclass
class QualityCheckResult:
    name: str
    status: str  # "PASS" | "FAIL"
    detail: str


@dataclass
class QualityReport:
    overall_status: str = "PASS"
    checks: list[QualityCheckResult] = field(default_factory=list)

    def add(self, result: QualityCheckResult) -> None:
        self.checks.append(result)
        if result.status == "FAIL":
            self.overall_status = "FAIL"

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([{"check": c.name, "status": c.status, "detail": c.detail} for c in self.checks])


def validate_schemas(cleaned: dict) -> list[QualityCheckResult]:
    results = []
    for table_name, schema in SCHEMAS.items():
        df = cleaned[table_name]
        try:
            schema.validate(df, lazy=True)
            results.append(QualityCheckResult(f"schema:{table_name}", "PASS", "no violations"))
        except pa.errors.SchemaErrors as exc:
            failure_cases = exc.failure_cases
            n_failed = len(failure_cases)
            pct = 100 * n_failed / max(len(df), 1)
            status = "FAIL" if pct > CRITICAL_ISSUE_MAX_PCT else "PASS"
            top = failure_cases["check"].value_counts().head(3).to_dict()
            results.append(
                QualityCheckResult(
                    f"schema:{table_name}", status,
                    f"{n_failed} rows ({pct:.2f}%) failed checks: {top}",
                )
            )
    return results


def check_referential_integrity(cleaned: dict) -> list[QualityCheckResult]:
    results = []

    loading_ids = set(cleaned["loading_events"]["loading_id"])
    dispatch_ids = set(cleaned["dispatch_events"]["dispatch_id"])
    invoice_ids = set(cleaned["invoices"]["invoice_id"])

    def orphan_check(name: str, child: pd.DataFrame, fk_col: str, valid_ids: set) -> QualityCheckResult:
        orphans = ~child[fk_col].isin(valid_ids)
        n_orphans = int(orphans.sum())
        pct = 100 * n_orphans / max(len(child), 1)
        status = "FAIL" if pct > ORPHAN_FK_MAX_PCT else "PASS"
        return QualityCheckResult(
            name, status, f"{n_orphans} orphan rows ({pct:.3f}%) referencing a non-existent parent"
        )

    results.append(orphan_check("referential_integrity:dispatch_to_loading",
                                 cleaned["dispatch_events"], "loading_id", loading_ids))
    results.append(orphan_check("referential_integrity:invoice_to_dispatch",
                                 cleaned["invoices"], "dispatch_id", dispatch_ids))
    results.append(orphan_check("referential_integrity:payment_to_invoice",
                                 cleaned["payments"], "invoice_id", invoice_ids))
    return results


def check_issue_thresholds(issues_df: pd.DataFrame, cleaned: dict) -> list[QualityCheckResult]:
    """Fail the gate if a 'critical' cleaning issue affected too large a
    share of a table's rows. 'warning' and 'exception' severities never
    fail the gate -- they are informational / business exceptions."""
    results = []
    if issues_df.empty:
        return results
    critical = issues_df[issues_df["severity"] == "critical"]
    for _, row in critical.iterrows():
        table_rows = max(len(cleaned.get(row["table"], [])), 1)
        pct = 100 * row["count"] / table_rows
        status = "FAIL" if pct > CRITICAL_ISSUE_MAX_PCT else "PASS"
        results.append(
            QualityCheckResult(
                f"critical_issue:{row['table']}.{row['check']}", status,
                f"{row['count']} rows ({pct:.2f}%)",
            )
        )
    return results


def run_quality_gate(cleaned: dict, issues_df: pd.DataFrame) -> QualityReport:
    report = QualityReport()
    for result in validate_schemas(cleaned):
        report.add(result)
    for result in check_referential_integrity(cleaned):
        report.add(result)
    for result in check_issue_thresholds(issues_df, cleaned):
        report.add(result)
    return report
