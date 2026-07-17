import pytest

from app.news_runtime_environment import (
    load_news_analysis_ttl_seconds,
    load_news_maximum_age_seconds,
)


def test_loads_news_analysis_ttl_seconds(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "NEWS_ANALYSIS_TTL_SECONDS",
        "1800",
    )

    assert (
        load_news_analysis_ttl_seconds()
        == 1800.0
    )


def test_uses_default_news_analysis_ttl(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "NEWS_ANALYSIS_TTL_SECONDS",
        raising=False,
    )

    assert (
        load_news_analysis_ttl_seconds()
        == 1800.0
    )


def test_rejects_non_positive_news_analysis_ttl(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "NEWS_ANALYSIS_TTL_SECONDS",
        "0",
    )

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        load_news_analysis_ttl_seconds()
        
def test_loads_news_maximum_age_seconds(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "NEWS_MAXIMUM_AGE_SECONDS",
        "3600",
    )

    assert (
        load_news_maximum_age_seconds()
        == 3600.0
    )


def test_uses_default_news_maximum_age(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "NEWS_MAXIMUM_AGE_SECONDS",
        raising=False,
    )

    assert (
        load_news_maximum_age_seconds()
        == 3600.0
    )


def test_rejects_non_positive_news_maximum_age(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "NEWS_MAXIMUM_AGE_SECONDS",
        "0",
    )

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        load_news_maximum_age_seconds()
        
