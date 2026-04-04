from datetime import date

import pandas as pd

from omnichannel_platform.batch.commerce_batch_ingestion import normalize_date_series


def test_normalize_date_series_converts_iso_strings_to_python_dates() -> None:
    series = pd.Series(["2018-01-01", "2018-12-31"])

    normalized = normalize_date_series(series)

    assert list(normalized) == [date(2018, 1, 1), date(2018, 12, 31)]
