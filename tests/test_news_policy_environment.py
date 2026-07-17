import pytest

from app.news_policy_environment import (
    load_news_policy_mode,
    load_news_policy_observation_path,
)


def test_loads_off_mode_by_default(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "NEWS_POLICY_MODE",
        raising=False,
    )

    assert (
        load_news_policy_mode()
        == "off"
    )


def test_loads_shadow_mode(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "NEWS_POLICY_MODE",
        " shadow ",
    )

    assert (
        load_news_policy_mode()
        == "shadow"
    )


def test_loads_enforce_mode(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "NEWS_POLICY_MODE",
        "enforce",
    )

    assert (
        load_news_policy_mode()
        == "enforce"
    )


def test_rejects_unknown_policy_mode(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "NEWS_POLICY_MODE",
        "observe",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported news policy mode",
    ):
        load_news_policy_mode()


def test_loads_default_observation_path(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "NEWS_POLICY_OBSERVATION_PATH",
        raising=False,
    )

    path = (
        load_news_policy_observation_path()
    )

    assert str(path) in {
        (
            "data\\"
            "news-policy-observations.jsonl"
        ),
        (
            "data/"
            "news-policy-observations.jsonl"
        ),
    }


def test_loads_configured_observation_path(
    monkeypatch,
    tmp_path,
) -> None:
    path = (
        tmp_path
        / "observations.jsonl"
    )

    monkeypatch.setenv(
        "NEWS_POLICY_OBSERVATION_PATH",
        str(path),
    )

    assert (
        load_news_policy_observation_path()
        == path
    )