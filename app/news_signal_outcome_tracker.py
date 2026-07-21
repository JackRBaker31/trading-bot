from dataclasses import dataclass
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from typing import Callable

from app.market_data import (
    MarketDataError,
    MarketDataProvider,
)
from app.news_signal import NewsSignal
from app.news_signal_outcome import (
    NewsSignalOutcome,
)
from app.news_signal_outcome_store import (
    NewsSignalOutcomeStore,
)
from app.news_signal_price_snapshot import (
    NewsSignalPriceSnapshot,
)


@dataclass(frozen=True)
class NewsOutcomeHorizon:
    name: str
    delay: timedelta

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError(
                "Horizon name is required."
            )

        if self.delay <= timedelta(0):
            raise ValueError(
                "Horizon delay must be positive."
            )


@dataclass(frozen=True)
class NewsSignalOutcomeSummary:
    eligible_count: int
    recorded_count: int
    skipped_existing_count: int
    missing_snapshot_count: int
    not_due_count: int
    failed_count: int
    deferred_count: int
    stale_quote_count: int
    failed_symbols: tuple[str, ...]


class NewsSignalOutcomeTracker:
    def __init__(
        self,
        *,
        market_data_provider: (
            MarketDataProvider
        ),
        outcome_store: (
            NewsSignalOutcomeStore
        ),
        reference_snapshot_provider: (
            Callable[
                [NewsSignal],
                NewsSignalPriceSnapshot | None,
            ]
        ),
        now_provider: (
            Callable[[], datetime] | None
        ) = None,
        horizons: tuple[
            NewsOutcomeHorizon,
            ...,
        ] | None = None,
        max_price_requests: int | None = None,
    ) -> None:
        if (
            max_price_requests is not None
            and max_price_requests <= 0
        ):
            raise ValueError(
                "Maximum price requests must be "
                "positive."
            )

        self.market_data_provider = (
            market_data_provider
        )
        self.outcome_store = (
            outcome_store
        )
        self.reference_snapshot_provider = (
            reference_snapshot_provider
        )
        self.now_provider = (
            now_provider
            or (
                lambda: datetime.now(
                    timezone.utc
                )
            )
        )
        self.horizons = (
            horizons
            or (
                NewsOutcomeHorizon(
                    name="1H",
                    delay=timedelta(hours=1),
                ),
                NewsOutcomeHorizon(
                    name="1D",
                    delay=timedelta(days=1),
                ),
                NewsOutcomeHorizon(
                    name="5D",
                    delay=timedelta(days=5),
                ),
            )
        )
        self.max_price_requests = (
            max_price_requests
        )

    def run(
        self,
        *,
        signals: list[NewsSignal],
    ) -> NewsSignalOutcomeSummary:
        now = self.now_provider()

        existing_keys = {
            (
                outcome.article_id,
                outcome.horizon_name,
            )
            for outcome
            in self.outcome_store.load_all()
        }

        eligible_count = 0
        recorded_count = 0
        skipped_existing_count = 0
        missing_snapshot_count = 0
        not_due_count = 0
        failed_count = 0
        deferred_count = 0
        stale_quote_count = 0
        price_request_count = 0
        failed_symbols: list[str] = []

        for signal in signals:
            snapshot = (
                self.reference_snapshot_provider(
                    signal
                )
            )

            if snapshot is None:
                missing_snapshot_count += 1
                continue

            due_horizons: list[
                NewsOutcomeHorizon
            ] = []

            for horizon in self.horizons:
                horizon_name = (
                    horizon.name.upper().strip()
                )
                key = (
                    signal.article_id,
                    horizon_name,
                )

                if key in existing_keys:
                    skipped_existing_count += 1
                    continue

                due_at = (
                    snapshot.captured_at
                    + horizon.delay
                )

                if now < due_at:
                    not_due_count += 1
                    continue

                due_horizons.append(
                    horizon
                )

            if not due_horizons:
                continue

            if (
                self.max_price_requests
                is not None
                and price_request_count
                >= self.max_price_requests
            ):
                deferred_count += len(
                    due_horizons
                )
                continue

            price_request_count += 1

            try:
                quote = (
                    self.market_data_provider
                    .get_price(
                        signal.symbol
                    )
                )
            except MarketDataError:
                failed_count += len(
                    due_horizons
                )

                if (
                    signal.symbol
                    not in failed_symbols
                ):
                    failed_symbols.append(
                        signal.symbol
                    )

                continue

            observed_at = quote.timestamp

            quote_has_not_advanced = (
                observed_at is not None
                and observed_at
                <= snapshot.captured_at
            )

            untimestamped_unchanged_quote = (
                observed_at is None
                and quote.price == snapshot.price
            )

            if (
                quote_has_not_advanced
                or untimestamped_unchanged_quote
            ):
                stale_quote_count += len(
                    due_horizons
                )
                continue

            for horizon in due_horizons:
                horizon_name = (
                    horizon.name.upper().strip()
                )
                eligible_count += 1

                return_percent = (
                    (
                        quote.price
                        - snapshot.price
                    )
                    / snapshot.price
                    * 100.0
                )

                outcome = NewsSignalOutcome(
                    article_id=(
                        signal.article_id
                    ),
                    symbol=signal.symbol,
                    horizon_name=(
                        horizon_name
                    ),
                    signal_published_at=(
                        signal.published_at
                    ),
                    observed_at=(
                        observed_at
                        or now
                    ),
                    reference_price=(
                        snapshot.price
                    ),
                    observed_price=(
                        quote.price
                    ),
                    return_percent=(
                        return_percent
                    ),
                )

                self.outcome_store.append(
                    outcome=outcome
                )
                existing_keys.add(
                    (
                        signal.article_id,
                        horizon_name,
                    )
                )
                recorded_count += 1

        return NewsSignalOutcomeSummary(
            eligible_count=eligible_count,
            recorded_count=recorded_count,
            skipped_existing_count=(
                skipped_existing_count
            ),
            missing_snapshot_count=(
                missing_snapshot_count
            ),
            not_due_count=not_due_count,
            failed_count=failed_count,
            deferred_count=deferred_count,
            stale_quote_count=stale_quote_count,
            failed_symbols=tuple(
                failed_symbols
            ),
        )