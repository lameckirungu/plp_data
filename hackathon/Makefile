.PHONY: setup generate-data pipeline test lint web-install web-dev web-build api-dev docker-build docker-run docker-stop

VENV := venv/bin

setup:
	python3 -m venv venv
	$(VENV)/pip install -q --upgrade pip
	$(VENV)/pip install -e ".[dev]"

generate-data:
	$(VENV)/python scripts/generate_synthetic_data.py

pipeline:
	$(VENV)/python -m o2c_pipeline.pipeline

test:
	$(VENV)/pytest -v

lint:
	$(VENV)/ruff check src/ tests/ scripts/ api/
	cd web && npm run lint

web-install:
	cd web && npm install

web-dev:
	cd web && npm run dev

web-build:
	cd web && npm run build

# Backend dev server, port 8010 (not 8000 -- avoids a common local conflict).
# The Vite dev server (web-dev) proxies /api to this.
api-dev:
	$(VENV)/uvicorn api.main:app --reload --port 8010

docker-build:
	docker build -t o2c-dashboard:latest .

docker-run:
	docker compose up --build

docker-stop:
	docker compose down
