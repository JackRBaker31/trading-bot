from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from app.market_data import (
    MarketDataProvider,
    PriceQuote,
)
from app.news_observation_service import (
    NewsObservationSummary,
)
from app.news_research_cycle_service import (
    NewsResearchCycleRequest,
    NewsResearchCycleService,
)
from app.news_signal import NewsSignal
from app.news_signal_store import NewsSignalStore


class FakeObservationService:
    def __init__(
        self,
        *,
        store_path: str,
        create_signal: bool,
    ) -> None:
        self._store = NewsSignalStore(
            file_path=store_path
        )
        self._create_signal = create_signal

    def run(
        self,
        *,
        symbols: list[str],
    ) -> NewsObservationSummary:
        cleaned_symbols = tuple(
            sorted(symbols)
        )

        if self._create_signal:
            published_at = datetime(
                2026,
                7,
                19,
                12,
                0,
                tzinfo=timezone.utc,
            )

            self._store.append(
                signal=NewsSignal(
                    article_id="article-1",
                    symbol="AAPL",
                    headline="Example",
                    sentiment=1.0,
                    relevance=1.0,
                    confidence=0.8,
                    event_type=(
                        "STOCK_SHORTTERM_POSITIVE"
                    ),
                    is_material=True,
                    published_at=published_at,
                    expires_at=(
                        published_at
                        + timedelta(days=1)
                    ),
                    source="test",
                    reasoning_summary="Example.",
                )
            )

        return NewsObservationSummary(
            article_count=(
                1 if self._create_signal else 0
            ),
            signal_count=(
                1 if self._create_signal else 0
            ),
            skipped_duplicate_count=0,
            symbols=cleaned_symbols,
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
            price=100.0,
            provider="FAKE",
        )


def test_runs_complete_cycle_and_returns_result(
    tmp_path,
) -> None:
    signals_path = str(
        tmp_path / "signals.jsonl"
    )

    service = NewsResearchCycleService(
        observation_service_factory=(
            lambda store_path: (
                FakeObservationService(
                    store_path=store_path,
                    create_signal=True,
                )
            )
        ),
        market_data_provider_factory=(
            lambda provider_name, symbols: (
                FakeMarketDataProvider()
            )
        ),
    )

    result = service.run(
        request=NewsResearchCycleRequest(
            symbols=("aapl",),
            provider_name="fake",
            signals_path=signals_path,
            snapshots_path=str(
                tmp_path / "snapshots.jsonl"
            ),
            outcomes_path=str(
                tmp_path / "outcomes.jsonl"
            ),
            max_price_requests=2,
        )
    )

    assert result.provider_name == "FAKE"
    assert result.symbols == ("AAPL",)
    assert (
        result.observation_summary.signal_count
        == 1
    )
    assert result.snapshot_summary is not None
    assert (
        result.snapshot_summary.captured_count
        == 1
    )
    assert result.outcome_summary is not None
    assert (
        result.outcome_summary.not_due_count
        == 3
    )
    assert result.research_summary.signal_count == 1
    assert result.research_summary.outcome_count == 0


def test_handles_cycle_with_no_signals(
    tmp_path,
) -> None:
    service = NewsResearchCycleService(
        observation_service_factory=(
            lambda store_path: (
                FakeObservationService(
                    store_path=store_path,
                    create_signal=False,
                )
            )
        ),
        market_data_provider_factory=(
            lambda provider_name, symbols: (
                FakeMarketDataProvider()
            )
        ),
    )

    result = service.run(
        request=NewsResearchCycleRequest(
            symbols=("AAPL",),
            provider_name="FAKE",
            signals_path=str(
                tmp_path / "signals.jsonl"
            ),
            snapshots_path=str(
                tmp_path / "snapshots.jsonl"
            ),
            outcomes_path=str(
                tmp_path / "outcomes.jsonl"
            ),
        )
    )

    assert result.snapshot_summary is None
    assert result.outcome_summary is None
    assert result.research_summary.signal_count == 0


def test_request_normalises_symbols_and_provider() -> None:
    request = NewsResearchCycleRequest(
        symbols=(
            " msft ",
            "AAPL",
            "aapl",
        ),
        provider_name=" twelve_data ",
    )

    assert request.symbols == (
        "AAPL",
        "MSFT",
    )
    assert request.market_data_provider == "TWELVE_DATA"


@pytest.mark.parametrize(
    "max_price_requests",
    [
        0,
        -1,
    ],
)
def test_request_rejects_invalid_price_budget(
    max_price_requests: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="positive",
    ):
        NewsResearchCycleRequest(
            symbols=("AAPL",),
            provider_name="FAKE",
            max_price_requests=(
                max_price_requests
            ),
        )