from datetime import date

import httpx
import pytest

from app.market_data import MarketDataError
from app.twelve_data_historical_data import (
    TwelveDataHistoricalDataClient,
)


class FakeResponse:
    def __init__(
        self,
        data: object,
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

    def json(self) -> object:
        return self._data


def test_returns_daily_bars_in_date_order(
    monkeypatch,
) -> None:
    requested: dict[str, object] = {}

    def fake_get(
        url: str,
        *,
        params: dict[str, object],
        timeout: float,
    ) -> FakeResponse:
        requested["url"] = url
        requested["params"] = params
        requested["timeout"] = timeout

        return FakeResponse(
            {
                "meta": {
                    "symbol": "AAPL",
                    "interval": "1day",
                },
                "values": [
                    {
                        "datetime": "2026-01-03",
                        "open": "101.0",
                        "high": "103.0",
                        "low": "100.0",
                        "close": "102.0",
                        "volume": "1200",
                    },
                    {
                        "datetime": "2026-01-02",
                        "open": "99.0",
                        "high": "102.0",
                        "low": "98.0",
                        "close": "101.0",
                        "volume": "1000",
                    },
                ],
                "status": "ok",
            }
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    client = TwelveDataHistoricalDataClient(
        api_key="test-key",
    )

    bars = client.get_daily_bars(
        symbol=" aapl ",
        output_size=500,
    )

    assert [
        bar.trading_date
        for bar in bars
    ] == [
        date(2026, 1, 2),
        date(2026, 1, 3),
    ]

    assert bars[0].symbol == "AAPL"
    assert bars[0].open_price == 99.0
    assert bars[0].high_price == 102.0
    assert bars[0].low_price == 98.0
    assert bars[0].close_price == 101.0
    assert bars[0].volume == 1000

    assert requested["url"] == (
        "https://api.twelvedata.com/time_series"
    )
    assert requested["params"] == {
        "symbol": "AAPL",
        "interval": "1day",
        "outputsize": 500,
        "apikey": "test-key",
    }
    assert requested["timeout"] == 10.0


def test_rejects_provider_error(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "status": "error",
                "message": "Invalid API key.",
            }
        ),
    )

    client = TwelveDataHistoricalDataClient(
        api_key="bad-key",
    )

    with pytest.raises(
        MarketDataError,
        match="Invalid API key",
    ):
        client.get_daily_bars(
            symbol="AAPL",
            output_size=100,
        )


def test_rejects_invalid_historical_bar(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "status": "ok",
                "values": [
                    {
                        "datetime": "2026-01-02",
                        "open": "invalid",
                    }
                ],
            }
        ),
    )

    client = TwelveDataHistoricalDataClient(
        api_key="test-key",
    )

    with pytest.raises(
        MarketDataError,
        match="invalid historical bar",
    ):
        client.get_daily_bars(
            symbol="AAPL",
            output_size=100,
        )


@pytest.mark.parametrize(
    ("api_key", "output_size", "message"),
    [
        ("", 100, "API key"),
        ("test-key", 0, "Output size"),
    ],
)
def test_rejects_invalid_configuration_or_request(
    api_key: str,
    output_size: int,
    message: str,
) -> None:
    if not api_key:
        with pytest.raises(
            ValueError,
            match=message,
        ):
            TwelveDataHistoricalDataClient(
                api_key=api_key,
            )
        return

    client = TwelveDataHistoricalDataClient(
        api_key=api_key,
    )

    with pytest.raises(
        ValueError,
        match=message,
    ):
        client.get_daily_bars(
            symbol="AAPL",
            output_size=output_size,
        )