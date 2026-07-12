import httpx
import pytest

from app.broker import BrokerError
from app.trading212_client import (
    Trading212Client,
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


def test_get_account_summary(
    monkeypatch,
) -> None:
    def fake_get(*args, **kwargs):
        return FakeResponse(
            {
                "id": 123456,
                "currency": "GBP",
                "cash": {
                    "availableToTrade": 9000,
                    "reservedForOrders": 100,
                    "inPies": 50,
                },
                "investments": {
                    "currentValue": 1000,
                    "totalCost": 950,
                    "realizedProfitLoss": 10,
                    "unrealizedProfitLoss": 50,
                },
                "totalValue": 10000,
            }
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    client = Trading212Client(
        api_key="key",
        api_secret="secret",
        environment="DEMO",
    )

    summary = client.get_account_summary()

    assert summary.account_id == 123456
    assert summary.currency == "GBP"
    assert summary.available_to_trade == 9000
    assert summary.total_value == 10000


def test_get_positions(
    monkeypatch,
) -> None:
    def fake_get(*args, **kwargs):
        return FakeResponse(
            [
                {
                    "instrument": {
                        "ticker": "AAPL_US_EQ"
                    },
                    "quantity": 5,
                    "averagePricePaid": 150,
                    "currentPrice": 155,
                    "profitLoss": 25,
                }
            ]
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    client = Trading212Client(
        api_key="key",
        api_secret="secret",
    )

    positions = client.get_positions()

    assert len(positions) == 1
    assert (
        positions[0].ticker
        == "AAPL_US_EQ"
    )
    assert positions[0].quantity == 5
    assert positions[0].profit_loss == 25


def test_invalid_credentials_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="API key",
    ):
        Trading212Client(
            api_key="",
            api_secret="secret",
        )

    with pytest.raises(
        ValueError,
        match="API secret",
    ):
        Trading212Client(
            api_key="key",
            api_secret="",
        )


def test_invalid_environment_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="DEMO or LIVE",
    ):
        Trading212Client(
            api_key="key",
            api_secret="secret",
            environment="UNKNOWN",
        )


def test_http_error_becomes_broker_error(
    monkeypatch,
) -> None:
    def fake_get(*args, **kwargs):
        return FakeResponse(
            {},
            status_code=401,
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    client = Trading212Client(
        api_key="bad",
        api_secret="bad",
    )

    with pytest.raises(
        BrokerError,
        match="HTTP 401",
    ):
        client.get_account_summary()


def test_invalid_summary_response_is_rejected(
    monkeypatch,
) -> None:
    def fake_get(*args, **kwargs):
        return FakeResponse(
            {
                "unexpected": "data"
            }
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    client = Trading212Client(
        api_key="key",
        api_secret="secret",
    )

    with pytest.raises(
        BrokerError,
        match="invalid account summary",
    ):
        client.get_account_summary()

def test_rate_limit_error_includes_reset_information(
    monkeypatch,
) -> None:
    request = httpx.Request(
        "GET",
        "https://example.com",
    )

    response = httpx.Response(
        429,
        request=request,
        headers={
            "x-ratelimit-reset": "1760000000",
            "x-ratelimit-remaining": "0",
        },
    )

    def fake_get(*args, **kwargs):
        return response

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    client = Trading212Client(
        api_key="key",
        api_secret="secret",
    )

    with pytest.raises(
        BrokerError,
        match="rate limit reached",
    ):
        client.get_account_summary()