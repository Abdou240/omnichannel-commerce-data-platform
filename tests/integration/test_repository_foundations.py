from pathlib import Path


def test_repository_contains_key_foundation_files() -> None:
    expected_paths = [
        Path(".dockerignore"),
        Path("Dockerfile"),
        Path("config/base.yaml"),
        Path("dashboard/app.py"),
        Path("docs/architecture.md"),
        Path("orchestration/kestra/flows/daily_platform_ingestion.yml"),
        Path("data/sample/batch/open_food_facts_products_sample.json"),
        Path("data/sample/streaming/retailrocket_events.jsonl"),
        Path("src/omnichannel_platform/api/main.py"),
        Path("src/omnichannel_platform/api/routes/orders.py"),
        Path("warehouse/dbt/dbt_project.yml"),
        Path("warehouse/dbt/macros/raw_relations.sql"),
        Path("warehouse/dbt/models/public_sources.yml"),
        Path("infra/terraform/gcp/main.tf"),
        Path("kafka/topics.yaml"),
        Path("quality/contracts/raw_olist_orders.yml"),
        Path("src/omnichannel_platform/quality/rules_catalog.py"),
        Path("src/omnichannel_platform/dashboard/logic.py"),
        Path("spark/jobs/clickstream_sessionization.py"),
    ]

    for expected_path in expected_paths:
        assert expected_path.exists(), f"Missing foundation file: {expected_path}"
