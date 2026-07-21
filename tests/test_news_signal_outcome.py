from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from app.news_signal_outcome import (
    NewsSignalOutcome,
)


def test_creates_news_signal_outcome() -> None:
    published_at = datetime(
        2026,
        7,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )

    outcome = NewsSignalOutcome(
        article_id="article-1",
        symbol="aapl",
        horizon_name="1h",
        signal_published_at=published_at,
        observed_at=(
            published_at
            + timedelta(hours=1)
        ),
        reference_price=100.0,
        observed_price=105.0,
        return_percent=5.0,
    )

    assert outcome.symbol == "AAPL"
    assert outcome.horizon_name == "1H"


def test_rejects_non_positive_price() -> None:
    now = datetime.now(
        timezone.utc
    )

    with pytest.raises(
        ValueError,
        match="Reference price",
    ):
        NewsSignalOutcome(
            article_id="article-1",
            symbol="AAPL",
            horizon_name="1H",
            signal_published_at=now,
            observed_at=now,
            reference_price=0.0,
            observed_price=100.0,
            return_percent=0.0,
        )