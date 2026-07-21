from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.market_data import (
    MarketDataProvider,
    PriceQuote,
)
from app.news_signal import NewsSignal
from app.news_signal_price_snapshot_service import (
    NewsSignalPriceSnapshotService,
)
from app.news_signal_price_snapshot_store import (
    NewsSignalPriceSnapshotStore,
)


class FakeMarketDataProvider(
    MarketDataProvider
):
    def get_price(
        self,
        symbol: str,
    ) -> PriceQuote:
        return PriceQuote(
            symbol=symbol,
            price=123.0,
            timestamp=datetime(
                2026,
                7,
                18,
                13,
                0,
                tzinfo=timezone.utc,
            ),
            provider="FAKE",
        )


def create_signal() -> NewsSignal:
    published_at = datetime(
        2026,
        7,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )
    return NewsSignal(
        article_id="article-1",
        symbol="AAPL",
        headline="Example",
        sentiment=1.0,
        relevance=1.0,
        confidence=0.8,
        event_type="STOCK_SHORTTERM_POSITIVE",
        is_material=True,
        published_at=published_at,
        expires_at=(
            published_at
            + timedelta(days=1)
        ),
        source="alpha_vantage",
        reasoning_summary="Example.",
    )


def test_captures_snapshot_once(
    tmp_path,
) -> None:
    store = NewsSignalPriceSnapshotStore(
        file_path=str(
            tmp_path / "snapshots.jsonl"
        )
    )
    service = NewsSignalPriceSnapshotService(
        market_data_provider=(
            FakeMarketDataProvider()
        ),
        snapshot_store=store,
    )

    first = service.run(
        signals=[create_signal()]
    )
    second = service.run(
        signals=[create_signal()]
    )

    assert first.captured_count == 1
    assert second.captured_count == 0
    assert (
        second.skipped_existing_count
        == 1
    )