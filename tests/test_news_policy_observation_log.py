from datetime import (
    datetime,
    timezone,
)

from app.news_analysis import (
    NewsSentiment,
)
from app.news_policy_observation import (
    NewsPolicyObservation,
)
from app.news_policy_observation_log import (
    NewsPolicyObservationLog,
)
from app.orders import (
    OrderSide,
)


def create_observation() -> NewsPolicyObservation:
    return NewsPolicyObservation(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=6,
        analysis_available=True,
        analysis_sentiment=(
            NewsSentiment.NEGATIVE
        ),
        analysis_expires_at=datetime(
            2026,
            7,
            17,
            12,
            30,
            tzinfo=timezone.utc,
        ),
        would_approve=False,
        reason=(
            "Negative stock-specific news "
            "blocks BUY orders."
        ),
        observed_at=datetime(
            2026,
            7,
            17,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )


def test_appends_and_reads_observations(
    tmp_path,
) -> None:
    log_path = (
        tmp_path
        / "news-policy-observations.jsonl"
    )

    log = NewsPolicyObservationLog(
        file_path=log_path,
    )

    observation = create_observation()

    log.append(
        observation
    )

    assert log.read_all() == [
        observation,
    ]


def test_appends_multiple_observations(
    tmp_path,
) -> None:
    log_path = (
        tmp_path
        / "news-policy-observations.jsonl"
    )

    log = NewsPolicyObservationLog(
        file_path=log_path,
    )

    first = create_observation()

    second = NewsPolicyObservation(
        symbol="MSFT",
        side=OrderSide.SELL,
        quantity=2,
        analysis_available=False,
        analysis_sentiment=None,
        analysis_expires_at=None,
        would_approve=True,
        reason=(
            "No current news analysis was available."
        ),
        observed_at=datetime(
            2026,
            7,
            17,
            12,
            5,
            tzinfo=timezone.utc,
        ),
    )

    log.append(
        first
    )
    log.append(
        second
    )

    assert log.read_all() == [
        first,
        second,
    ]


def test_returns_empty_list_when_log_missing(
    tmp_path,
) -> None:
    log = NewsPolicyObservationLog(
        file_path=(
            tmp_path
            / "missing.jsonl"
        ),
    )

    assert log.read_all() == []