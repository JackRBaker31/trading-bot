import httpx
import pytest

from app.market_data import MarketDataError
from app.twelve_data_market_data import (
    TwelveDataMarketDataProvider,
)


class FakeResponse:
    def __init__(
        self,
        data: dict[str, object],
        status_code: int = 200,
    ) -> None:
        self._data = data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request(
                "GET",
                "https://example.com",
            )

            response = httpx.Response(
                self.status_code,
                request=request,
            )

            raise httpx.HTTPStatusError(
                "Request failed.",
                request=request,
                response=response,
            )

    def json(self) -> dict[str, object]:
        return self._data
class FakeHttpClient:
    def __init__(self) -> None:
        self.requested_url: str | None = None
        self.requested_params: dict[str, object] | None = None
        self.requested_timeout: float | None = None

    def get(
        self,
        url: str,
        *,
        params: dict[str, object],
        timeout: float,
    ) -> FakeResponse:
        self.requested_url = url
        self.requested_params = params
        self.requested_timeout = timeout

        return FakeResponse(
            {
                "symbol": "AAPL",
                "close": "210.50",
            }
        )

def test_provider_returns_valid_quote(
    monkeypatch,
) -> None:
    def fake_get(*args, **kwargs) -> FakeResponse:
        return FakeResponse(
            {
                "symbol": "AAPL",
                "close": "210.50",
            }
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    provider = TwelveDataMarketDataProvider(
        api_key="test-key"
    )

    quote = provider.get_price("aapl")

    assert quote.symbol == "AAPL"
    assert quote.price == 210.50
    assert quote.provider == "TWELVE_DATA"
    assert quote.timestamp is not None


def test_provider_rejects_api_error(
    monkeypatch,
) -> None:
    def fake_get(*args, **kwargs) -> FakeResponse:
        return FakeResponse(
            {
                "status": "error",
                "message": "Invalid API key.",
            }
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    provider = TwelveDataMarketDataProvider(
        api_key="bad-key"
    )

    with pytest.raises(
        MarketDataError,
        match="Invalid API key",
    ):
        provider.get_price("AAPL")


def test_provider_rejects_missing_price(
    monkeypatch,
) -> None:
    def fake_get(*args, **kwargs) -> FakeResponse:
        return FakeResponse(
            {
                "symbol": "AAPL",
            }
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    provider = TwelveDataMarketDataProvider(
        api_key="test-key"
    )

    with pytest.raises(
        MarketDataError,
        match="No closing price",
    ):
        provider.get_price("AAPL")


def test_provider_converts_timeout_to_market_data_error(
    monkeypatch,
) -> None:
    def fake_get(*args, **kwargs):
        raise httpx.TimeoutException(
            "Timed out."
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    provider = TwelveDataMarketDataProvider(
        api_key="test-key"
    )

    with pytest.raises(
        MarketDataError,
        match="timed out",
    ):
        provider.get_price("AAPL")


def test_provider_requires_api_key() -> None:
    with pytest.raises(
        ValueError,
        match="API key",
    ):
        TwelveDataMarketDataProvider(
            api_key=""
        )

def test_provider_rejects_non_object_json(
    monkeypatch,
) -> None:
    def fake_get(*args, **kwargs) -> FakeResponse:
        return FakeResponse([])  # type: ignore[arg-type]

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    provider = TwelveDataMarketDataProvider(
        api_key="test-key"
    )

    with pytest.raises(
        MarketDataError,
        match="invalid response",
    ):
        provider.get_price("AAPL")

def test_provider_rejects_non_numeric_price(
    monkeypatch,
) -> None:
    def fake_get(*args, **kwargs) -> FakeResponse:
        return FakeResponse(
            {
                "symbol": "AAPL",
                "close": "not-a-number",
            }
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    provider = TwelveDataMarketDataProvider(
        api_key="test-key"
    )

    with pytest.raises(
        MarketDataError,
        match="Invalid price",
    ):
        provider.get_price("AAPL")

def test_provider_rejects_symbol_mismatch(
    monkeypatch,
) -> None:
    def fake_get(*args, **kwargs) -> FakeResponse:
        return FakeResponse(
            {
                "symbol": "MSFT",
                "close": "210.50",
            }
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    provider = TwelveDataMarketDataProvider(
        api_key="test-key"
    )

    with pytest.raises(
        MarketDataError,
        match="symbol",
    ):
        provider.get_price("AAPL")

def test_provider_retries_timeout_once(
    monkeypatch,
) -> None:
    call_count = 0

    def fake_get(*args, **kwargs) -> FakeResponse:
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            raise httpx.TimeoutException(
                "Timed out."
            )

        return FakeResponse(
            {
                "symbol": "AAPL",
                "close": "210.50",
            }
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    provider = TwelveDataMarketDataProvider(
        api_key="test-key",
        max_attempts=2,
    )

    quote = provider.get_price("AAPL")

    assert quote.price == 210.50
    assert call_count == 2