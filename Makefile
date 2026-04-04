PYTHON ?= python3
ENVIRONMENT ?= dev
WAREHOUSE_PATH ?= storage/warehouse/local.duckdb
KAFKA_BROKER ?= localhost:9092
DBT_PROFILES_DIR ?= .dbt
TF_DIR ?= infra/terraform/gcp
TF_VARS_FILE ?= $(TF_DIR)/terraform.tfvars
GCP_PROJECT_ID ?= demo-project-id
GCP_REGION ?= us-central1
ARTIFACT_REPO ?= omnichannel-platform
DASHBOARD_IMAGE ?= $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT_ID)/$(ARTIFACT_REPO)/dashboard:latest
API_IMAGE ?= $(GCP_REGION)-docker.pkg.dev/$(GCP_PROJECT_ID)/$(ARTIFACT_REPO)/api:latest
DASHBOARD_PORT ?= 8501

.PHONY: install install-dev install-local lint test pre-commit up down logs tree \
	run-batch run-streaming run-warehouse-plan run-warehouse run-quality run-serving \
	run-dashboard run-api dbt-build-ci kestra-info kafka-topics spark-sessionize \
	docker-build-pipeline docker-build-dashboard docker-build-api terraform-init-gcp \
	terraform-plan-gcp terraform-apply-gcp deploy-dashboard-gcp

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

install-local:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev,batch,streaming,warehouse,nosql,quality,dashboard,api]"

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

run-dashboard:
	streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port $(DASHBOARD_PORT)

run-api:
	uvicorn omnichannel_platform.api.main:app --host 0.0.0.0 --port 8000 --reload

kestra-info:
	@echo "Kestra flow lives under orchestration/kestra/flows/daily_platform_ingestion.yml"
	@echo "TODO: run inside a worker image with project dependencies installed"

kafka-topics:
	bash kafka/create_topics.sh $(KAFKA_BROKER)

spark-sessionize:
	spark-submit spark/jobs/clickstream_sessionization.py --input-path data/sample/streaming/retailrocket_events.jsonl --output-path storage/gold/retailrocket_sessions

docker-build-pipeline:
	docker build --target pipeline -t omnichannel-platform-pipeline:local .

docker-build-dashboard:
	docker build --target dashboard -t $(DASHBOARD_IMAGE) .

docker-build-api:
	docker build --target api -t $(API_IMAGE) .

terraform-init-gcp:
	terraform -chdir=$(TF_DIR) init

terraform-plan-gcp:
	terraform -chdir=$(TF_DIR) plan -var-file=$(TF_VARS_FILE) -var="dashboard_container_image=$(DASHBOARD_IMAGE)"

terraform-apply-gcp:
	terraform -chdir=$(TF_DIR) apply -var-file=$(TF_VARS_FILE) -var="dashboard_container_image=$(DASHBOARD_IMAGE)"

deploy-dashboard-gcp: docker-build-dashboard
	@echo "Authenticate Docker before pushing, for example: gcloud auth configure-docker $(GCP_REGION)-docker.pkg.dev"
	docker push $(DASHBOARD_IMAGE)
	$(MAKE) terraform-apply-gcp
