from omnichannel_platform.batch.commerce_batch_ingestion import _seed_olist_frames


def test_olist_seed_produces_deterministic_output() -> None:
    first_run = _seed_olist_frames()
    second_run = _seed_olist_frames()

    for table_name in first_run:
        assert table_name in second_run
        assert len(first_run[table_name]) == len(second_run[table_name])
        assert list(first_run[table_name].columns) == list(second_run[table_name].columns)
        assert first_run[table_name].iloc[0].to_dict() == second_run[table_name].iloc[0].to_dict()


def test_olist_seed_row_counts_match_expectation() -> None:
    frames = _seed_olist_frames()

    assert len(frames["olist_orders_dataset.csv"]) == 500
    assert len(frames["olist_customers_dataset.csv"]) == 250
    assert len(frames["olist_products_dataset.csv"]) == 150
    assert len(frames["olist_order_payments_dataset.csv"]) == 500
    assert len(frames["olist_order_items_dataset.csv"]) > 0
