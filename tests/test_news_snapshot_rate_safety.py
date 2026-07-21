from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.market_data import (
    MarketDataError,
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


class PartlyFailingProvider(
    MarketDataProvider
):
    def get_price(
        self,
        symbol: str,
    ) -> PriceQuote:
        if symbol == "V":
            raise MarketDataError(
                "Rate limited."
            )

        return PriceQuote(
            symbol=symbol,
            price=100.0,
            provider="FAKE",
        )


def create_signal(
    *,
    article_id: str,
    symbol: str,
) -> NewsSignal:
    published_at = datetime.now(
        timezone.utc
    )

    return NewsSignal(
        article_id=article_id,
        symbol=symbol,
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


def test_continues_after_market_data_failure(
    tmp_path,
) -> None:
    store = NewsSignalPriceSnapshotStore(
        file_path=str(
            tmp_path / "snapshots.jsonl"
        )
    )

    summary = NewsSignalPriceSnapshotService(
        market_data_provider=(
            PartlyFailingProvider()
        ),
        snapshot_store=store,
    ).run(
        signals=[
            create_signal(
                article_id="v-1",
                symbol="V",
            ),
            create_signal(
                article_id="xom-1",
                symbol="XOM",
            ),
        ]
    )

    assert summary.failed_count == 1
    assert summary.captured_count == 1
    assert summary.failed_symbols == (
        "V",
    )


def test_defers_requests_over_budget(
    tmp_path,
) -> None:
    store = NewsSignalPriceSnapshotStore(
        file_path=str(
            tmp_path / "snapshots.jsonl"
        )
    )

    summary = NewsSignalPriceSnapshotService(
        market_data_provider=(
            PartlyFailingProvider()
        ),
        snapshot_store=store,
        max_price_requests=1,
    ).run(
        signals=[
            create_signal(
                article_id="aapl-1",
                symbol="AAPL",
            ),
            create_signal(
                article_id="xom-1",
                symbol="XOM",
            ),
        ]
    )

    assert summary.captured_count == 1
    assert summary.deferred_count == 1