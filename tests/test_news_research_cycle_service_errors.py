import pytest

from app.application_errors import (
    ConfigurationError,
    ProviderUnavailableError,
    ResearchRunError,
)
from app.news_research_cycle_service import (
    NewsResearchCycleRequest,
    NewsResearchCycleService,
)


class FailingObservationService:
    def run(
        self,
        *,
        symbols: list[str],
    ):
        raise RuntimeError(
            "Provider transport failed."
        )


class EmptyObservationService:
    def run(
        self,
        *,
        symbols: list[str],
    ):
        from app.news_observation_service import (
            NewsObservationSummary,
        )

        return NewsObservationSummary(
            symbols=tuple(symbols),
            article_count=0,
            signal_count=0,
            skipped_duplicate_count=0,
        )


def test_request_raises_configuration_error() -> None:
    with pytest.raises(
        ConfigurationError,
        match="At least one symbol",
    ):
        NewsResearchCycleRequest(
            symbols=(),
            provider_name="TWELVE_DATA",
        )


def test_wraps_observation_failure() -> None:
    service = NewsResearchCycleService(
        observation_service_factory=(
            lambda _: FailingObservationService()
        ),
        market_data_provider_factory=(
            lambda provider, symbols: None
        ),
    )

    with pytest.raises(
        ResearchRunError,
        match="observation stage",
    ) as captured:
        service.run(
            request=NewsResearchCycleRequest(
                symbols=("AAPL",),
                provider_name="TWELVE_DATA",
            )
        )

    assert isinstance(
        captured.value.__cause__,
        RuntimeError,
    )
    assert (
        captured.value.code
        == "NEWS_OBSERVATION_FAILED"
    )
    assert captured.value.retryable is True
    assert captured.value.context == {
        "stage": "observation",
        "symbols": ["AAPL"],
    }


def test_wraps_provider_factory_failure(
    tmp_path,
) -> None:
    signals_path = tmp_path / "signals.jsonl"

    from datetime import (
        datetime,
        timedelta,
        timezone,
    )
    from app.news_signal import NewsSignal
    from app.news_signal_store import (
        NewsSignalStore,
    )

    published_at = datetime.now(
        timezone.utc
    )

    NewsSignalStore(
        file_path=str(signals_path)
    ).append(
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

    service = NewsResearchCycleService(
        observation_service_factory=(
            lambda _: EmptyObservationService()
        ),
        market_data_provider_factory=(
            lambda provider, symbols: (
                (_ for _ in ())
                .throw(
                    RuntimeError(
                        "Factory failure."
                    )
                )
            )
        ),
    )

    with pytest.raises(
        ProviderUnavailableError,
        match="could not be initialized",
    ) as captured:
        service.run(
            request=NewsResearchCycleRequest(
                symbols=("AAPL",),
                provider_name="TWELVE_DATA",
                signals_path=str(
                    signals_path
                ),
                snapshots_path=str(
                    tmp_path / "snapshots.jsonl"
                ),
                outcomes_path=str(
                    tmp_path / "outcomes.jsonl"
                ),
            )
        )

    assert isinstance(
        captured.value.__cause__,
        RuntimeError,
    )
    assert (
        captured.value.code
        == (
            "MARKET_DATA_PROVIDER_"
            "INITIALIZATION_FAILED"
        )
    )
    assert captured.value.retryable is True
    assert captured.value.context == {
        "provider": "TWELVE_DATA",
        "symbols": ["AAPL"],
    }