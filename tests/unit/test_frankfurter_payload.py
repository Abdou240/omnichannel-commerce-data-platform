from datetime import datetime, timezone

from omnichannel_platform.batch.commerce_batch_ingestion import normalize_frankfurter_payload


def test_normalize_frankfurter_payload_handles_v2_rate_list() -> None:
    ingested_at = datetime(2026, 4, 4, 9, 0, tzinfo=timezone.utc)
    payload = [
        {"date": "2018-01-01", "base": "EUR", "quote": "USD", "rate": 1.1974},
        {"date": "2018-01-01", "base": "EUR", "quote": "BRL", "rate": 3.9633},
    ]

    rows = normalize_frankfurter_payload(payload, ingested_at)

    assert rows == [
        {
            "rate_date": "2018-01-01",
            "base_currency": "EUR",
            "quote_currency": "USD",
            "fx_rate": 1.1974,
            "ingested_at": ingested_at,
        },
        {
            "rate_date": "2018-01-01",
            "base_currency": "EUR",
            "quote_currency": "BRL",
            "fx_rate": 3.9633,
            "ingested_at": ingested_at,
        },
    ]
