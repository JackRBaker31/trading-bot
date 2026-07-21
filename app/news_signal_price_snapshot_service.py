from dataclasses import dataclass
from datetime import (
    datetime,
    timezone,
)
from typing import Callable

from app.market_data import (
    MarketDataError,
    MarketDataProvider,
)
from app.news_signal import NewsSignal
from app.news_signal_price_snapshot import (
    NewsSignalPriceSnapshot,
)
from app.news_signal_price_snapshot_store import (
    NewsSignalPriceSnapshotStore,
)


@dataclass(frozen=True)
class NewsSignalPriceSnapshotSummary:
    signal_count: int
    captured_count: int
    skipped_existing_count: int
    failed_count: int
    deferred_count: int
    failed_symbols: tuple[str, ...]


class NewsSignalPriceSnapshotService:
    def __init__(
        self,
        *,
        market_data_provider: (
            MarketDataProvider
        ),
        snapshot_store: (
            NewsSignalPriceSnapshotStore
        ),
        now_provider: (
            Callable[[], datetime] | None
        ) = None,
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
        self.snapshot_store = (
            snapshot_store
        )
        self.now_provider = (
            now_provider
            or (
                lambda: datetime.now(
                    timezone.utc
                )
            )
        )
        self.max_price_requests = (
            max_price_requests
        )

    def run(
        self,
        *,
        signals: list[NewsSignal],
    ) -> NewsSignalPriceSnapshotSummary:
        captured_count = 0
        skipped_existing_count = 0
        failed_count = 0
        deferred_count = 0
        price_request_count = 0
        failed_symbols: list[str] = []

        for signal in signals:
            existing = (
                self.snapshot_store
                .get_by_article_id(
                    signal.article_id
                )
            )

            if existing is not None:
                skipped_existing_count += 1
                continue

            if (
                self.max_price_requests
                is not None
                and price_request_count
                >= self.max_price_requests
            ):
                deferred_count += 1
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
                failed_count += 1

                if (
                    signal.symbol
                    not in failed_symbols
                ):
                    failed_symbols.append(
                        signal.symbol
                    )

                continue

            snapshot = NewsSignalPriceSnapshot(
                article_id=signal.article_id,
                symbol=signal.symbol,
                captured_at=(
                    quote.timestamp
                    or self.now_provider()
                ),
                price=quote.price,
                provider=quote.provider,
            )

            self.snapshot_store.append(
                snapshot=snapshot
            )
            captured_count += 1

        return NewsSignalPriceSnapshotSummary(
            signal_count=len(signals),
            captured_count=captured_count,
            skipped_existing_count=(
                skipped_existing_count
            ),
            failed_count=failed_count,
            deferred_count=deferred_count,
            failed_symbols=tuple(
                failed_symbols
            ),
        )