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
from app.news_signal_outcome_store import (
    NewsSignalOutcomeStore,
)
from app.news_signal_outcome_tracker import (
    NewsOutcomeHorizon,
    NewsSignalOutcomeTracker,
)
from app.news_signal_price_snapshot import (
    NewsSignalPriceSnapshot,
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
            price=110.0,
            provider="FAKE",
        )

class OldTimestampMarketDataProvider(
    MarketDataProvider
):
    def __init__(
        self,
        *,
        timestamp: datetime,
    ) -> None:
        self.timestamp = timestamp

    def get_price(
        self,
        symbol: str,
    ) -> PriceQuote:
        return PriceQuote(
            symbol=symbol,
            price=101.0,
            provider="TEST",
            timestamp=self.timestamp,
        )


class UnchangedMarketDataProvider(
    MarketDataProvider
):
    def get_price(
        self,
        symbol: str,
    ) -> PriceQuote:
        return PriceQuote(
            symbol=symbol,
            price=100.0,
            provider="TEST",
            timestamp=None,
        )


def create_signal() -> NewsSignal:
    published_at = datetime(
        2026,
        7,
        18,
        10,
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


def create_snapshot() -> NewsSignalPriceSnapshot:
    return NewsSignalPriceSnapshot(
        article_id="article-1",
        symbol="AAPL",
        captured_at=datetime(
            2026,
            7,
            18,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        price=100.0,
        provider="FAKE",
    )


def test_horizon_starts_from_snapshot_time(
    tmp_path,
) -> None:
    signal = create_signal()
    snapshot = create_snapshot()

    tracker = NewsSignalOutcomeTracker(
        market_data_provider=(
            FakeMarketDataProvider()
        ),
        outcome_store=NewsSignalOutcomeStore(
            file_path=str(
                tmp_path / "outcomes.jsonl"
            )
        ),
        reference_snapshot_provider=(
            lambda current: snapshot
        ),
        now_provider=lambda: datetime(
            2026,
            7,
            18,
            12,
            30,
            tzinfo=timezone.utc,
        ),
        horizons=(
            NewsOutcomeHorizon(
                name="1H",
                delay=timedelta(hours=1),
            ),
        ),
    )

    summary = tracker.run(
        signals=[signal]
    )

    assert summary.recorded_count == 0
    assert summary.not_due_count == 1


def test_records_due_snapshot_outcome(
    tmp_path,
) -> None:
    signal = create_signal()
    snapshot = create_snapshot()
    store = NewsSignalOutcomeStore(
        file_path=str(
            tmp_path / "outcomes.jsonl"
        )
    )

    tracker = NewsSignalOutcomeTracker(
        market_data_provider=(
            FakeMarketDataProvider()
        ),
        outcome_store=store,
        reference_snapshot_provider=(
            lambda current: snapshot
        ),
        now_provider=lambda: datetime(
            2026,
            7,
            18,
            13,
            30,
            tzinfo=timezone.utc,
        ),
        horizons=(
            NewsOutcomeHorizon(
                name="1H",
                delay=timedelta(hours=1),
            ),
        ),
    )

    summary = tracker.run(
        signals=[signal]
    )

    assert summary.recorded_count == 1
    assert (
        store.load_all()[0]
        .return_percent
        == 10.0
    )

def test_defers_quote_with_old_timestamp(
    tmp_path,
) -> None:
    captured_at = datetime(
        2026,
        7,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )

    signal = create_signal()

    snapshot = NewsSignalPriceSnapshot(
        article_id=signal.article_id,
        symbol=signal.symbol,
        captured_at=captured_at,
        price=100.0,
        provider="TEST",
    )

    provider = OldTimestampMarketDataProvider(
        timestamp=captured_at,
    )

    tracker = NewsSignalOutcomeTracker(
        market_data_provider=provider,
        outcome_store=(
            NewsSignalOutcomeStore(
                file_path=str(
                    tmp_path / "outcomes.jsonl"
                )
            )
        ),
        reference_snapshot_provider=(
            lambda _: snapshot
        ),
        now_provider=lambda: (
            captured_at
            + timedelta(hours=2)
        ),
        horizons=(
            NewsOutcomeHorizon(
                name="1H",
                delay=timedelta(hours=1),
            ),
        ),
    )

    summary = tracker.run(
        signals=[signal]
    )

    assert summary.recorded_count == 0
    assert summary.stale_quote_count == 1

def test_defers_untimestamped_unchanged_quote(
    tmp_path,
) -> None:
    captured_at = datetime(
        2026,
        7,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )

    signal = create_signal()

    snapshot = NewsSignalPriceSnapshot(
        article_id=signal.article_id,
        symbol=signal.symbol,
        captured_at=captured_at,
        price=100.0,
        provider="TEST",
    )

    provider = UnchangedMarketDataProvider()

    tracker = NewsSignalOutcomeTracker(
        market_data_provider=provider,
        outcome_store=(
            NewsSignalOutcomeStore(
                file_path=str(
                    tmp_path / "outcomes.jsonl"
                )
            )
        ),
        reference_snapshot_provider=(
            lambda _: snapshot
        ),
        now_provider=lambda: (
            captured_at
            + timedelta(hours=2)
        ),
        horizons=(
            NewsOutcomeHorizon(
                name="1H",
                delay=timedelta(hours=1),
            ),
        ),
    )

    summary = tracker.run(
        signals=[signal]
    )

    assert summary.recorded_count == 0
    assert summary.stale_quote_count == 1