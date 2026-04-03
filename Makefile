PYTHON ?= python3
ENVIRONMENT ?= dev
WAREHOUSE_PATH ?= storage/warehouse/local.duckdb
KAFKA_BROKER ?= localhost:9092
DBT_PROFILES_DIR ?= .dbt

.PHONY: install install-dev install-local lint test pre-commit up down logs tree \
	run-batch run-streaming run-warehouse-plan run-warehouse run-quality run-serving \
	dbt-build-ci kestra-info kafka-topics spark-sessionize

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

install-local:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev,batch,streaming,warehouse,nosql,quality]"

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
	$(PYTHON) -m omnichannel_platform.batch.commerce_batch_ingestion --env $(ENVIRONMENT)

run-streaming:
	$(PYTHON) -m omnichannel_platform.streaming.clickstream_consumer --env $(ENVIRONMENT) --mode replay

run-warehouse-plan:
	$(PYTHON) -m omnichannel_platform.warehouse.layer_catalog --env $(ENVIRONMENT)

dbt-build-ci:
	mkdir -p $(DBT_PROFILES_DIR)
	mkdir -p storage/warehouse
	cp warehouse/dbt/profiles.ci.yml $(DBT_PROFILES_DIR)/profiles.yml
	WAREHOUSE_PATH=$(WAREHOUSE_PATH) dbt build --project-dir warehouse/dbt --profiles-dir $(DBT_PROFILES_DIR)

run-warehouse: run-warehouse-plan dbt-build-ci

run-quality:
	$(PYTHON) -m omnichannel_platform.quality.rules_catalog

run-serving:
	@echo "TODO: implement serving-layer sync entry point"

kestra-info:
	@echo "Kestra flow lives under orchestration/kestra/flows/daily_platform_ingestion.yml"
	@echo "TODO: run inside a worker image with project dependencies installed"

kafka-topics:
	bash kafka/create_topics.sh $(KAFKA_BROKER)

spark-sessionize:
	spark-submit spark/jobs/clickstream_sessionization.py --input-path data/sample/streaming/retailrocket_events.jsonl --output-path storage/gold/retailrocket_sessions
