.PHONY: setup generate-data pipeline test lint dashboard docker-build docker-run docker-stop

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
	$(VENV)/ruff check src/ tests/ scripts/ app/

dashboard:
	$(VENV)/streamlit run app/dashboard.py

docker-build:
	docker build -t o2c-dashboard:latest .

docker-run:
	docker compose up --build

docker-stop:
	docker compose down
