PYTHON ?= python3

.PHONY: install install-dev lint test pre-commit up down logs tree run-batch run-streaming run-warehouse run-quality run-serving dbt-parse kestra-info kafka-topics spark-starter

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	ruff check .

test:
	pytest

pre-commit:
	pre-commit run --all-files

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

tree:
	find . -maxdepth 4 | sort

run-batch:
	$(PYTHON) -m omnichannel_platform.batch.commerce_batch_ingestion --env $${ENVIRONMENT:-dev}

run-streaming:
	$(PYTHON) -m omnichannel_platform.streaming.clickstream_consumer --env $${ENVIRONMENT:-dev} --mode replay

run-warehouse:
	$(PYTHON) -m omnichannel_platform.warehouse.layer_catalog --env $${ENVIRONMENT:-dev}

run-quality:
	$(PYTHON) -m omnichannel_platform.quality.rules_catalog

run-serving:
	@echo "TODO: implement serving-layer sync entry point"

dbt-parse:
	@echo "TODO: run 'dbt parse --project-dir warehouse/dbt' after configuring the Postgres or BigQuery target"

kestra-info:
	@echo "Kestra flow skeletons live under orchestration/kestra/flows"
	@echo "TODO: validate or deploy flows via Kestra CLI or API once the runtime is available"

kafka-topics:
	@echo "Kafka topic definitions live under kafka/topics.yaml"
	@echo "TODO: run kafka/create_topics.sh against Redpanda or a managed Kafka cluster"

spark-starter:
	@echo "Spark starter job lives under spark/jobs/clickstream_sessionization.py"
	@echo "TODO: submit with spark-submit once Spark is installed or containerized"
