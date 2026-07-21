from datetime import (
    datetime,
    timezone,
)

import pytest

from app.news_signal_price_snapshot import (
    NewsSignalPriceSnapshot,
)


def test_creates_price_snapshot() -> None:
    snapshot = NewsSignalPriceSnapshot(
        article_id="article-1",
        symbol="aapl",
        captured_at=datetime.now(
            timezone.utc
        ),
        price=100.0,
        provider="fake",
    )

    assert snapshot.symbol == "AAPL"
    assert snapshot.provider == "FAKE"


def test_rejects_invalid_snapshot_price() -> None:
    with pytest.raises(
        ValueError,
        match="Snapshot price",
    ):
        NewsSignalPriceSnapshot(
            article_id="article-1",
            symbol="AAPL",
            captured_at=datetime.now(
                timezone.utc
            ),
            price=0.0,
            provider="FAKE",
        )