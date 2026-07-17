import pytest

from app.alpha_vantage_news_environment import (
    load_alpha_vantage_api_key,
)


def test_loads_alpha_vantage_api_key(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "ALPHA_VANTAGE_API_KEY",
        " test-key ",
    )

    assert (
        load_alpha_vantage_api_key()
        == "test-key"
    )


def test_rejects_missing_alpha_vantage_api_key(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "ALPHA_VANTAGE_API_KEY",
        raising=False,
    )

    with pytest.raises(
        ValueError,
        match="ALPHA_VANTAGE_API_KEY",
    ):
        load_alpha_vantage_api_key()