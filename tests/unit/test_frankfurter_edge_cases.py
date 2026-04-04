from datetime import datetime, timezone

from omnichannel_platform.batch.commerce_batch_ingestion import normalize_frankfurter_payload


def test_normalize_frankfurter_payload_skips_incomplete_entries() -> None:
    ingested_at = datetime(2026, 4, 4, 9, 0, tzinfo=timezone.utc)
    payload = [
        {"date": "2018-01-01", "base": "EUR", "quote": "USD", "rate": 1.19},
        {"date": "2018-01-01", "base": "EUR"},  # missing quote + rate
        {"base": "EUR", "quote": "BRL", "rate": 3.96},  # missing date
        {"date": "2018-01-02", "base": "EUR", "quote": "USD", "rate": None},  # rate None
    ]

    rows = normalize_frankfurter_payload(payload, ingested_at)

    assert len(rows) == 1
    assert rows[0]["quote_currency"] == "USD"
    assert rows[0]["fx_rate"] == 1.19


def test_normalize_frankfurter_payload_handles_empty_list() -> None:
    ingested_at = datetime(2026, 4, 4, 9, 0, tzinfo=timezone.utc)

    rows = normalize_frankfurter_payload([], ingested_at)

    assert rows == []
