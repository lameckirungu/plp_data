#!/bin/sh
# Always regenerate the reconciliation output at container start so a
# deployed image's dashboard reflects its own code + data, never a stale
# snapshot baked in at build time from a different commit.
set -e

echo "Running order-to-cash pipeline (ingest -> clean -> quality gate -> reconcile)..."
python -m o2c_pipeline.pipeline

echo "Starting dashboard..."
exec streamlit run app/dashboard.py \
  --server.address=0.0.0.0 \
  --server.port=8501 \
  --server.headless=true \
  --browser.gatherUsageStats=false
