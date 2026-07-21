from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from app.news_signal import NewsSignal


def create_signal(
    **overrides,
) -> NewsSignal:
    published_at = datetime(
        2026,
        7,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )

    values = {
        "article_id": "article-1",
        "symbol": "aapl",
        "headline": "Apple raises guidance",
        "sentiment": 0.7,
        "relevance": 0.9,
        "confidence": 0.8,
        "event_type": "guidance_raised",
        "is_material": True,
        "published_at": published_at,
        "expires_at": (
            published_at
            + timedelta(hours=24)
        ),
        "source": "Example News",
        "reasoning_summary": (
            "Guidance increased."
        ),
    }
    values.update(overrides)
    return NewsSignal(**values)


def test_normalises_signal_text() -> None:
    signal = create_signal()

    assert signal.symbol == "AAPL"
    assert (
        signal.event_type
        == "GUIDANCE_RAISED"
    )


@pytest.mark.parametrize(
    (
        "field_name",
        "value",
        "message",
    ),
    [
        (
            "sentiment",
            1.1,
            "Sentiment",
        ),
        (
            "relevance",
            -0.1,
            "Relevance",
        ),
        (
            "confidence",
            1.1,
            "Confidence",
        ),
    ],
)
def test_rejects_invalid_scores(
    field_name: str,
    value: float,
    message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=message,
    ):
        create_signal(
            **{
                field_name: value
            }
        )


def test_rejects_invalid_expiry() -> None:
    published_at = datetime(
        2026,
        7,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        ValueError,
        match="Expiry",
    ):
        create_signal(
            published_at=published_at,
            expires_at=published_at,
        )