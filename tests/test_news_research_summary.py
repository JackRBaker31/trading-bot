from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.news_research_summary import (
    summarize_news_research,
)
from app.news_signal import NewsSignal
from app.news_signal_outcome import (
    NewsSignalOutcome,
)


def create_signal(
    *,
    article_id: str,
    sentiment: float,
    confidence: float,
    is_material: bool,
    event_type: str,
) -> NewsSignal:
    published_at = datetime(
        2026,
        7,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )

    return NewsSignal(
        article_id=article_id,
        symbol="AAPL",
        headline="Example",
        sentiment=sentiment,
        relevance=1.0,
        confidence=confidence,
        event_type=event_type,
        is_material=is_material,
        published_at=published_at,
        expires_at=(
            published_at
            + timedelta(days=1)
        ),
        source="alpha_vantage",
        reasoning_summary="Example.",
    )


def create_outcome(
    *,
    article_id: str,
    return_percent: float,
    horizon_name: str = "1D",
) -> NewsSignalOutcome:
    published_at = datetime(
        2026,
        7,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )

    return NewsSignalOutcome(
        article_id=article_id,
        symbol="AAPL",
        horizon_name=horizon_name,
        signal_published_at=published_at,
        observed_at=(
            published_at
            + timedelta(days=1)
        ),
        reference_price=100.0,
        observed_price=(
            100.0
            * (
                1.0
                + return_percent
                / 100.0
            )
        ),
        return_percent=return_percent,
    )


def test_summarizes_sentiment_and_direction() -> None:
    summary = summarize_news_research(
        signals=[
            create_signal(
                article_id="positive-1",
                sentiment=1.0,
                confidence=0.95,
                is_material=True,
                event_type="GUIDANCE_RAISED",
            ),
            create_signal(
                article_id="negative-1",
                sentiment=-1.0,
                confidence=0.80,
                is_material=True,
                event_type="GUIDANCE_CUT",
            ),
        ],
        outcomes=[
            create_outcome(
                article_id="positive-1",
                return_percent=4.0,
            ),
            create_outcome(
                article_id="negative-1",
                return_percent=-3.0,
            ),
        ],
    )

    positive = next(
        group
        for group in summary.sentiment_groups
        if group.group_name == "POSITIVE"
    )
    negative = next(
        group
        for group in summary.sentiment_groups
        if group.group_name == "NEGATIVE"
    )

    assert (
        positive.directional_success_percent
        == 100.0
    )
    assert (
        negative.directional_success_percent
        == 100.0
    )
    assert (
        negative.positive_return_percent
        == 0.0
    )


def test_tracks_unmatched_outcomes() -> None:
    summary = summarize_news_research(
        signals=[],
        outcomes=[
            create_outcome(
                article_id="missing",
                return_percent=1.0,
            )
        ],
    )

    assert summary.unmatched_outcome_count == 1
    assert summary.sentiment_groups == ()