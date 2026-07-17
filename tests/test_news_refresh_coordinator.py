from app.news_refresh_coordinator import (
    NewsRefreshCoordinator,
)


class FakeProvider:
    def __init__(
        self,
        stored_by_symbol: dict[str, object],
    ) -> None:
        self._stored_by_symbol = (
            stored_by_symbol
        )

    def get_stored_analysis(
        self,
        symbol: str,
    ) -> object | None:
        return self._stored_by_symbol.get(
            symbol
        )


class RecordingRefreshService:
    def __init__(
        self,
    ) -> None:
        self.refreshed_symbols: list[str] = []

    def refresh_symbol(
        self,
        *,
        symbol: str,
        model_name: str = "unknown",
        prompt_version: str = "unknown",
    ) -> None:
        self.refreshed_symbols.append(
            symbol
        )


def test_refreshes_only_missing_symbols() -> None:
    provider = FakeProvider(
        stored_by_symbol={
            "AAPL": object(),
        }
    )

    refresh_service = (
        RecordingRefreshService()
    )

    coordinator = NewsRefreshCoordinator(
        provider=provider,
        refresh_service=refresh_service,
    )

    result = coordinator.refresh_missing_or_expired(
        symbols=[
            " aapl ",
            "MSFT",
        ]
    )

    assert result.refreshed_symbols == (
        "MSFT",
    )
    assert result.skipped_symbols == (
        "AAPL",
    )
    assert result.failed_symbols == ()

    assert (
        refresh_service.refreshed_symbols
        == [
            "MSFT",
        ]
    )
    
class FailingRefreshService:
    def refresh_symbol(
        self,
        *,
        symbol: str,
        model_name: str = "unknown",
        prompt_version: str = "unknown",
    ) -> None:
        raise ValueError(
            f"No article found for {symbol}."
        )


def test_reports_refresh_failures_without_raising() -> None:
    coordinator = NewsRefreshCoordinator(
        provider=FakeProvider(
            stored_by_symbol={}
        ),
        refresh_service=FailingRefreshService(),
    )

    result = coordinator.refresh_missing_or_expired(
        symbols=[
            "AAPL",
            "MSFT",
        ]
    )

    assert result.refreshed_symbols == ()
    assert result.skipped_symbols == ()
    assert result.failed_symbols == (
        "AAPL",
        "MSFT",
    )