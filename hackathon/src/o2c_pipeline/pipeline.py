"""End-to-end orchestration: ingest -> clean -> quality gate -> reconcile ->
write outputs. This is the single entry point both CI and the dashboard's
"re-run pipeline" action call, so there is exactly one place that defines
what a pipeline run means and what "done" looks like.
"""

import json
import logging
import time
from datetime import UTC, datetime

from o2c_pipeline import clean, ingest, narrative, quality, reconcile, report
from o2c_pipeline import roi as roi_module
from o2c_pipeline.config import (
    DATA_PROCESSED_DIR,
    DQ_ISSUES_LOG,
    LEAKAGE_SUMMARY_JSON,
    RECONCILED_OUTPUT,
    REPORTS_DIR,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("o2c_pipeline")

PIPELINE_RUN_LOG = REPORTS_DIR / "pipeline_run_log.json"


class DataQualityGateError(RuntimeError):
    """Raised when the data-quality gate fails and the pipeline must halt
    before reconciliation runs on data that cannot be trusted."""


def run_pipeline(strict: bool = True) -> dict:
    started = time.time()
    run_meta = {"run_at": datetime.now(UTC).isoformat(), "status": "RUNNING"}

    try:
        logger.info("Ingesting raw source files")
        raw = ingest.read_all()
        row_counts_raw = {k: len(v) for k, v in raw.items()}
        logger.info("Raw row counts: %s", row_counts_raw)

        logger.info("Cleaning and normalizing")
        cleaned, issues_df = clean.clean_all(raw)
        row_counts_clean = {k: len(v) for k, v in cleaned.items()}
        logger.info("Clean row counts: %s", row_counts_clean)

        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        issues_df.to_csv(DQ_ISSUES_LOG, index=False)

        logger.info("Running data-quality gate")
        gate_report = quality.run_quality_gate(cleaned, issues_df)
        logger.info("Quality gate status: %s", gate_report.overall_status)
        for check in gate_report.checks:
            level = logging.WARNING if check.status == "FAIL" else logging.INFO
            logger.log(level, "  [%s] %s: %s", check.status, check.name, check.detail)

        if gate_report.overall_status == "FAIL" and strict:
            raise DataQualityGateError(
                "Data-quality gate failed -- see reports/pipeline_run_log.json for details"
            )

        logger.info("Reconciling order-to-cash cycle")
        reconciled = reconcile.reconcile(cleaned)
        multi_invoice = reconcile.multi_invoice_exceptions(cleaned)

        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        reconciled.to_csv(RECONCILED_OUTPUT, index=False)

        summary = reconcile.overall_summary(reconciled)
        summary["by_depot"] = reconcile.summarize_by(reconciled, "depot").to_dict(orient="records")
        summary["by_product"] = reconcile.summarize_by(reconciled, "product").to_dict(orient="records")
        summary["by_customer"] = (
            reconcile.summarize_by(reconciled, "customer")
            .head(10)
            .to_dict(orient="records")
        )
        summary["multi_invoice_exception_count"] = int(len(multi_invoice))
        summary["data_quality"] = {
            "overall_status": gate_report.overall_status,
            "checks": [c.__dict__ for c in gate_report.checks],
            "issues": issues_df.to_dict(orient="records"),
        }

        logger.info("Computing ROI and generating narratives")
        roi_result = roi_module.compute_roi(summary)
        summary["roi"] = roi_result
        summary["executive_narrative"] = narrative.generate_executive_narrative(summary, roi_result)
        summary["alert_narratives"] = narrative.generate_alert_narratives(reconciled)

        with open(LEAKAGE_SUMMARY_JSON, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info("Generating chart")
        report.generate_leakage_chart(reconciled, summary)

        duration = time.time() - started
        run_meta.update(
            status="SUCCESS",
            duration_seconds=round(duration, 2),
            row_counts_raw=row_counts_raw,
            row_counts_clean=row_counts_clean,
            quality_gate_status=gate_report.overall_status,
            total_leakage_kes=summary["total_leakage_kes"],
            exception_count=summary["exception_count"],
        )
        logger.info("Pipeline completed in %.2fs", duration)
        return summary

    except Exception as exc:  # noqa: BLE001 -- top-level run boundary, must record failure state
        run_meta.update(status="FAILED", error=str(exc), duration_seconds=round(time.time() - started, 2))
        logger.exception("Pipeline run failed")
        raise
    finally:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(PIPELINE_RUN_LOG, "w") as f:
            json.dump(run_meta, f, indent=2, default=str)


if __name__ == "__main__":
    run_pipeline()
