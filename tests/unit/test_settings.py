from omnichannel_platform.common.settings import deep_merge, load_settings


def test_deep_merge_overrides_nested_values() -> None:
    merged = deep_merge(
        {"sources": {"olist": {"extract_mode": "full_refresh"}}},
        {"sources": {"olist": {"extract_mode": "incremental"}}},
    )

    assert merged["sources"]["olist"]["extract_mode"] == "incremental"


def test_load_settings_reads_environment_override() -> None:
    settings = load_settings("dev")

    assert settings["runtime"]["environment"] == "dev"
    assert settings["sources"]["retailrocket"]["raw_topic"] == "retailrocket.events.raw"
