FROM python:3.12-slim

WORKDIR /app

# Install the package first so dependency layers cache independently of
# application code churn.
COPY pyproject.toml ./
COPY src/ src/
RUN pip install --no-cache-dir .

COPY app/ app/
COPY scripts/ scripts/
COPY data/ data/
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8501/_stcore/health')" || exit 1

ENTRYPOINT ["./docker-entrypoint.sh"]
