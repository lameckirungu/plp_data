#!/bin/sh
# Always regenerate the reconciliation output at container start so a
# deployed image's dashboard reflects its own code + data, never a stale
# snapshot baked in at build time from a different commit.
set -e

echo "Running order-to-cash pipeline (ingest -> clean -> quality gate -> reconcile)..."
python -m o2c_pipeline.pipeline

echo "Starting API + dashboard on :8000..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8000
