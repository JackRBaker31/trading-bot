from app.news_policy_observation_log import (
    NewsPolicyObservationLog,
)
from app.news_policy_runtime_factory import (
    create_news_policy_runtime,
)


def test_creates_disabled_runtime_by_default(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "NEWS_POLICY_MODE",
        raising=False,
    )

    runtime = create_news_policy_runtime()

    assert not runtime.config.enabled
    assert runtime.observation_log is None


def test_creates_shadow_runtime_with_log(
    monkeypatch,
    tmp_path,
) -> None:
    observation_path = (
        tmp_path
        / "observations.jsonl"
    )

    monkeypatch.setenv(
        "NEWS_POLICY_MODE",
        "shadow",
    )
    monkeypatch.setenv(
        "NEWS_POLICY_OBSERVATION_PATH",
        str(observation_path),
    )

    runtime = create_news_policy_runtime()

    assert runtime.config.shadow_mode
    assert isinstance(
        runtime.observation_log,
        NewsPolicyObservationLog,
    )


def test_creates_enforce_runtime_with_log(
    monkeypatch,
    tmp_path,
) -> None:
    observation_path = (
        tmp_path
        / "observations.jsonl"
    )

    monkeypatch.setenv(
        "NEWS_POLICY_MODE",
        "enforce",
    )
    monkeypatch.setenv(
        "NEWS_POLICY_OBSERVATION_PATH",
        str(observation_path),
    )

    runtime = create_news_policy_runtime()

    assert runtime.config.enforce_mode
    assert isinstance(
        runtime.observation_log,
        NewsPolicyObservationLog,
    )