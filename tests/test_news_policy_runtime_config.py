from pathlib import Path

from app.news_policy_runtime_config import (
    NewsPolicyRuntimeConfig,
)


def test_off_mode_disables_policy() -> None:
    config = NewsPolicyRuntimeConfig(
        mode="off",
        observation_path=Path(
            "data/observations.jsonl"
        ),
    )

    assert not config.enabled
    assert not config.shadow_mode
    assert not config.enforce_mode
    assert not config.observation_enabled


def test_shadow_mode_records_without_enforcement() -> None:
    config = NewsPolicyRuntimeConfig(
        mode="shadow",
        observation_path=Path(
            "data/observations.jsonl"
        ),
    )

    assert config.enabled
    assert config.shadow_mode
    assert not config.enforce_mode
    assert config.observation_enabled


def test_enforce_mode_blocks_rejected_orders() -> None:
    config = NewsPolicyRuntimeConfig(
        mode="enforce",
        observation_path=Path(
            "data/observations.jsonl"
        ),
    )

    assert config.enabled
    assert not config.shadow_mode
    assert config.enforce_mode
    assert config.observation_enabled