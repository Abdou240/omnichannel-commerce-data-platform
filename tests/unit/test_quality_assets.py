from omnichannel_platform.quality.rules_catalog import list_quality_assets


def test_quality_assets_include_contracts_and_expectations() -> None:
    assets = list_quality_assets()

    assert "quality/contracts/raw_olist_orders.yml" in assets["contracts"]
    assert "quality/expectations/raw_retailrocket_event_types.sql" in assets["expectations"]
    assert (
        "quality/expectations/reference_open_food_facts_products_not_null.sql"
        in assets["expectations"]
    )
