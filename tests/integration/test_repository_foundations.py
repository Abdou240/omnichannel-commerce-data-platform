from pathlib import Path


def test_repository_contains_key_foundation_files() -> None:
    expected_paths = [
        Path("config/base.yaml"),
        Path("docs/architecture.md"),
        Path("orchestration/kestra/flows/daily_platform_ingestion.yml"),
        Path("data/sample/streaming/retailrocket_events.jsonl"),
        Path("warehouse/dbt/dbt_project.yml"),
        Path("infra/terraform/gcp/main.tf"),
        Path("kafka/topics.yaml"),
        Path("quality/contracts/raw_olist_orders.yml"),
        Path("spark/jobs/clickstream_sessionization.py"),
    ]

    for expected_path in expected_paths:
        assert expected_path.exists(), f"Missing foundation file: {expected_path}"
