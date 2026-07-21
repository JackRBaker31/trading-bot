from collections.abc import Callable
from dataclasses import dataclass

from app.application_errors import (
    ApplicationError,
    ConfigurationError,
    DataStoreError,
    ProviderUnavailableError,
    ResearchRunError,
)
from app.market_data import MarketDataProvider
from app.news_observation_service import (
    NewsObservationService,
    NewsObservationSummary,
)
from app.news_research_summary import (
    NewsResearchSummary,
    summarize_news_research,
)
from app.news_signal_outcome_store import (
    NewsSignalOutcomeStore,
)
from app.news_signal_outcome_tracker import (
    NewsSignalOutcomeSummary,
    NewsSignalOutcomeTracker,
)
from app.news_signal_price_snapshot_service import (
    NewsSignalPriceSnapshotService,
    NewsSignalPriceSnapshotSummary,
)
from app.news_signal_price_snapshot_store import (
    NewsSignalPriceSnapshotStore,
)
from app.news_signal_store import NewsSignalStore
from app.run_history import RunType
from app.run_history_service import RunHistoryService


ObservationServiceFactory = Callable[
    [str],
    NewsObservationService,
]

MarketDataProviderFactory = Callable[
    [str, list[str]],
    MarketDataProvider,
]


@dataclass(frozen=True)
class NewsResearchCycleRequest:
    symbols: tuple[str, ...]
    provider_name: str
    signals_path: str = (
        "data/news_signals.jsonl"
    )
    snapshots_path: str = (
        "data/"
        "news_signal_price_snapshots.jsonl"
    )
    outcomes_path: str = (
        "data/news_signal_outcomes.jsonl"
    )
    max_price_requests: int = 5

    def __post_init__(self) -> None:
        cleaned_symbols = tuple(
            sorted(
                {
                    symbol.upper().strip()
                    for symbol in self.symbols
                    if symbol.strip()
                }
            )
        )

        if not cleaned_symbols:
            raise ConfigurationError(
                "At least one symbol is required."
            )

        cleaned_provider = (
            self.provider_name.upper().strip()
        )

        if not cleaned_provider:
            raise ConfigurationError(
                "Market-data provider is required."
            )

        if self.max_price_requests <= 0:
            raise ConfigurationError(
                "Maximum price requests must be "
                "positive."
            )

        for path_name, path_value in (
            ("Signals path", self.signals_path),
            ("Snapshots path", self.snapshots_path),
            ("Outcomes path", self.outcomes_path),
        ):
            if not path_value.strip():
                raise ConfigurationError(
                    f"{path_name} is required."
                )

        object.__setattr__(
            self,
            "symbols",
            cleaned_symbols,
        )
        object.__setattr__(
            self,
            "provider_name",
            cleaned_provider,
        )


@dataclass(frozen=True)
class NewsResearchCycleResult:
    provider_name: str
    symbols: tuple[str, ...]
    observation_summary: (
        NewsObservationSummary
    )
    snapshot_summary: (
        NewsSignalPriceSnapshotSummary
        | None
    )
    outcome_summary: (
        NewsSignalOutcomeSummary
        | None
    )
    research_summary: NewsResearchSummary


class NewsResearchCycleService:
    def __init__(
        self,
        *,
        observation_service_factory: (
            ObservationServiceFactory
        ),
        market_data_provider_factory: (
            MarketDataProviderFactory
        ),
        run_history_service: (
            RunHistoryService | None
        ) = None,
    ) -> None:
        self._observation_service_factory = (
            observation_service_factory
        )
        self._market_data_provider_factory = (
            market_data_provider_factory
        )
        self._run_history_service = (
            run_history_service
        )

    def run(
        self,
        *,
        request: NewsResearchCycleRequest,
    ) -> NewsResearchCycleResult:
        history_record = None

        if self._run_history_service is not None:
            history_record = (
                self._run_history_service.start_run(
                    run_type=(
                        RunType.NEWS_RESEARCH_CYCLE
                    ),
                    provider=request.provider_name,
                    symbols=request.symbols,
                    metadata={
                        "signals_path": request.signals_path,
                        "snapshots_path": request.snapshots_path,
                        "outcomes_path": request.outcomes_path,
                        "max_price_requests": (
                            request.max_price_requests
                        ),
                    },
                )
            )

        try:
            result = self._run_cycle(
                request=request
            )
        except Exception as error:
            if (
                history_record is not None
                and self._run_history_service
                is not None
            ):
                self._run_history_service.fail_run(
                    run_id=history_record.run_id,
                    error=error,
                )
            raise

        if (
            history_record is not None
            and self._run_history_service
            is not None
        ):
            snapshot = result.snapshot_summary
            outcome = result.outcome_summary

            self._run_history_service.complete_run(
                run_id=history_record.run_id,
                created_count=(
                    result.observation_summary.signal_count
                    + (
                        0
                        if snapshot is None
                        else snapshot.captured_count
                    )
                    + (
                        0
                        if outcome is None
                        else outcome.recorded_count
                    )
                ),
                skipped_count=(
                    result.observation_summary
                    .skipped_duplicate_count
                    + (
                        0
                        if snapshot is None
                        else snapshot.skipped_existing_count
                    )
                    + (
                        0
                        if outcome is None
                        else outcome.skipped_existing_count
                    )
                ),
                failure_count=(
                    (
                        0
                        if snapshot is None
                        else snapshot.failed_count
                    )
                    + (
                        0
                        if outcome is None
                        else outcome.failed_count
                    )
                ),
                metadata={
                    "articles_fetched": (
                        result.observation_summary.article_count
                    ),
                    "signals_total": (
                        result.research_summary.signal_count
                    ),
                    "outcomes_total": (
                        result.research_summary.outcome_count
                    ),
                    "outcomes_not_due": (
                        0
                        if outcome is None
                        else outcome.not_due_count
                    ),
                    "snapshots_deferred": (
                        0
                        if snapshot is None
                        else snapshot.deferred_count
                    ),
                    "outcomes_deferred": (
                        0
                        if outcome is None
                        else outcome.deferred_count
                    ),
                    "stale_outcomes_deferred": (
                        0
                        if outcome is None
                        else outcome.stale_quote_count
                    ),
                },
            )

        return result

    def _run_cycle(
        self,
        *,
        request: NewsResearchCycleRequest,
    ) -> NewsResearchCycleResult:
        try:
            observation_service = (
                self._observation_service_factory(
                    request.signals_path
                )
            )

            observation_summary = (
                observation_service.run(
                    symbols=list(request.symbols)
                )
            )
        except ApplicationError:
            raise
        except Exception as error:
            raise ResearchRunError(
                "News observation stage failed.",
                code=(
                    "NEWS_OBSERVATION_FAILED"
                ),
                retryable=True,
                context={
                    "stage": "observation",
                    "symbols": list(
                        request.symbols
                    ),
                },
            ) from error

        try:
            signal_store = NewsSignalStore(
                file_path=request.signals_path
            )
            signals = signal_store.load_all()

            snapshot_store = (
                NewsSignalPriceSnapshotStore(
                    file_path=request.snapshots_path
                )
            )
            outcome_store = (
                NewsSignalOutcomeStore(
                    file_path=request.outcomes_path
                )
            )
        except ApplicationError:
            raise
        except Exception as error:
            raise DataStoreError(
                "News research data could not be loaded.",
                code=(
                    "NEWS_RESEARCH_DATA_LOAD_FAILED"
                ),
                context={
                    "stage": "load",
                },
            ) from error

        snapshot_summary = None
        outcome_summary = None

        if signals:
            signal_symbols = sorted(
                {
                    signal.symbol
                    for signal in signals
                }
            )

            try:
                market_data_provider = (
                    self._market_data_provider_factory(
                        request.provider_name,
                        signal_symbols,
                    )
                )
            except ApplicationError:
                raise
            except Exception as error:
                raise ProviderUnavailableError(
                    "Market-data provider could not "
                    "be initialized.",
                    code=(
                        "MARKET_DATA_PROVIDER_"
                        "INITIALIZATION_FAILED"
                    ),
                    context={
                        "provider": (
                            request.provider_name
                        ),
                        "symbols": (
                            signal_symbols
                        ),
                    },
                ) from error

            try:
                snapshot_summary = (
                    NewsSignalPriceSnapshotService(
                        market_data_provider=(
                            market_data_provider
                        ),
                        snapshot_store=(
                            snapshot_store
                        ),
                        max_price_requests=(
                            request
                            .max_price_requests
                        ),
                    )
                    .run(
                        signals=signals
                    )
                )

                outcome_summary = (
                    NewsSignalOutcomeTracker(
                        market_data_provider=(
                            market_data_provider
                        ),
                        outcome_store=outcome_store,
                        reference_snapshot_provider=(
                            lambda signal: (
                                snapshot_store
                                .get_by_article_id(
                                    signal.article_id
                                )
                            )
                        ),
                        max_price_requests=(
                            request
                            .max_price_requests
                        ),
                    )
                    .run(
                        signals=signals
                    )
                )
            except ApplicationError:
                raise
            except Exception as error:
                raise ResearchRunError(
                    "News price measurement stage "
                    "failed.",
                    code=(
                        "NEWS_PRICE_MEASUREMENT_FAILED"
                    ),
                    retryable=True,
                    context={
                        "stage": (
                            "price_measurement"
                        ),
                        "provider": (
                            request.provider_name
                        ),
                    },
                ) from error

        try:
            outcomes = outcome_store.load_all()

            research_summary = (
                summarize_news_research(
                    signals=signals,
                    outcomes=outcomes,
                )
            )
        except ApplicationError:
            raise
        except Exception as error:
            raise DataStoreError(
                "News research results could not "
                "be loaded or summarized.",
                code=(
                    "NEWS_RESEARCH_SUMMARY_FAILED"
                ),
                context={
                    "stage": "summary",
                },
            ) from error

        return NewsResearchCycleResult(
            provider_name=request.provider_name,
            symbols=observation_summary.symbols,
            observation_summary=(
                observation_summary
            ),
            snapshot_summary=snapshot_summary,
            outcome_summary=outcome_summary,
            research_summary=research_summary,
        )