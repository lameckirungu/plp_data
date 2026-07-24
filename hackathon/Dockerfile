# ---- frontend build stage ----
FROM node:22-slim AS frontend-build
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# ---- python runtime stage ----
FROM python:3.12-slim
WORKDIR /app

# Install the package first so dependency layers cache independently of
# application code churn.
COPY pyproject.toml ./
COPY src/ src/
RUN pip install --no-cache-dir .

COPY api/ api/
COPY scripts/ scripts/
COPY data/ data/
COPY --from=frontend-build /app/web/dist ./web/dist
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8000/api/health')" || exit 1

ENTRYPOINT ["./docker-entrypoint.sh"]
