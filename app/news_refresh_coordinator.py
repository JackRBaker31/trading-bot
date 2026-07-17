import logging
from dataclasses import dataclass
from typing import Protocol


logger = logging.getLogger(__name__)


class StoredAnalysisProvider(Protocol):
    def get_stored_analysis(
        self,
        symbol: str,
    ) -> object | None:
        ...


class SymbolRefreshService(Protocol):
    def refresh_symbol(
        self,
        *,
        symbol: str,
        model_name: str = "unknown",
        prompt_version: str = "unknown",
    ) -> object:
        ...


@dataclass(frozen=True)
class NewsRefreshCoordinatorResult:
    refreshed_symbols: tuple[str, ...]
    skipped_symbols: tuple[str, ...]
    failed_symbols: tuple[str, ...]


class NewsRefreshCoordinator:
    def __init__(
        self,
        *,
        provider: StoredAnalysisProvider,
        refresh_service: SymbolRefreshService,
    ) -> None:
        self._provider = provider
        self._refresh_service = refresh_service

    def refresh_missing_or_expired(
        self,
        *,
        symbols: list[str],
        model_name: str = "unknown",
        prompt_version: str = "unknown",
    ) -> NewsRefreshCoordinatorResult:
        refreshed_symbols: list[str] = []
        skipped_symbols: list[str] = []
        failed_symbols: list[str] = []

        for symbol in symbols:
            normalised_symbol = (
                symbol.upper().strip()
            )

            if not normalised_symbol:
                continue

            stored_analysis = (
                self._provider
                .get_stored_analysis(
                    normalised_symbol
                )
            )

            if stored_analysis is not None:
                skipped_symbols.append(
                    normalised_symbol
                )
                continue

            try:
                self._refresh_service.refresh_symbol(
                    symbol=normalised_symbol,
                    model_name=model_name,
                    prompt_version=prompt_version,
                )
            except (
                RuntimeError,
                ValueError,
            ) as error:
                logger.warning(
                    "news_refresh_failed "
                    "symbol=%s error=%s",
                    normalised_symbol,
                    error,
                )

                failed_symbols.append(
                    normalised_symbol
                )
                continue

            refreshed_symbols.append(
                normalised_symbol
            )

        return NewsRefreshCoordinatorResult(
            refreshed_symbols=tuple(
                refreshed_symbols
            ),
            skipped_symbols=tuple(
                skipped_symbols
            ),
            failed_symbols=tuple(
                failed_symbols
            ),
        )