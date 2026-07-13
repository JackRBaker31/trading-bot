import httpx
import pytest

from app.broker import BrokerError
from app.trading212_client import (
    Trading212Client,
)
from app.broker import (
    BrokerError,
    BrokerOrderRejectedError,
    BrokerOrderSubmissionUnknownError,
    BrokerResourceNotFoundError,
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

def test_market_order_http_rejection_has_specific_type(
    monkeypatch,
) -> None:
    request = httpx.Request(
        "POST",
        "https://example.com",
    )

    response = httpx.Response(
        403,
        request=request,
        json={
            "error": "Order permission denied.",
        },
    )

    def fake_post(
        url,
        auth,
        json,
        timeout,
    ):
        return response

    monkeypatch.setattr(
        httpx,
        "post",
        fake_post,
    )

    client = Trading212Client(
        api_key="key",
        api_secret="secret",
        environment="DEMO",
    )

    with pytest.raises(
        BrokerOrderRejectedError,
        match="Order permission denied",
    ):
        client.place_market_order(
            ticker="AAPL_US_EQ",
            quantity=1,
        )

def test_market_order_timeout_is_submission_unknown(
    monkeypatch,
) -> None:
    def fake_post(
        url,
        auth,
        json,
        timeout,
    ):
        raise httpx.ReadTimeout(
            "Request timed out."
        )

    monkeypatch.setattr(
        httpx,
        "post",
        fake_post,
    )

    client = Trading212Client(
        api_key="key",
        api_secret="secret",
        environment="DEMO",
    )

    with pytest.raises(
        BrokerOrderSubmissionUnknownError,
        match="timed out",
    ):
        client.place_market_order(
            ticker="AAPL_US_EQ",
            quantity=1,
        )

def test_invalid_market_order_json_is_submission_unknown(
    monkeypatch,
) -> None:
    class InvalidJsonResponse(FakeResponse):
        def json(self) -> object:
            raise ValueError(
                "Invalid JSON."
            )

    def fake_post(
        url,
        auth,
        json,
        timeout,
    ):
        return InvalidJsonResponse(
            data=None
        )

    monkeypatch.setattr(
        httpx,
        "post",
        fake_post,
    )

    client = Trading212Client(
        api_key="key",
        api_secret="secret",
        environment="DEMO",
    )

    with pytest.raises(
        BrokerOrderSubmissionUnknownError,
        match="invalid JSON",
    ):
        client.place_market_order(
            ticker="AAPL_US_EQ",
            quantity=1,
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

def test_place_market_buy_order(
    monkeypatch,
) -> None:
    captured_request: dict[str, object] = {}

    def fake_post(
        url,
        auth,
        json,
        timeout,
    ):
        captured_request["url"] = url
        captured_request["json"] = json

        return FakeResponse(
            {
                "id": 987654,
                "ticker": "AAPL_US_EQ",
                "quantity": 1,
                "side": "BUY",
                "status": "NEW",
                "type": "MARKET",
                "filledQuantity": 0,
                "filledValue": 0,
                "currency": "GBP",
            }
        )

    monkeypatch.setattr(
        httpx,
        "post",
        fake_post,
    )

    client = Trading212Client(
        api_key="key",
        api_secret="secret",
        environment="DEMO",
    )

    result = client.place_market_order(
        ticker="aapl_us_eq",
        quantity=1,
    )

    assert result.order_id == 987654
    assert result.ticker == "AAPL_US_EQ"
    assert result.side == "BUY"
    assert result.order_type == "MARKET"

    assert captured_request["json"] == {
        "ticker": "AAPL_US_EQ",
        "quantity": 1,
        "extendedHours": False,
    }


def test_place_market_sell_order_uses_negative_quantity(
    monkeypatch,
) -> None:
    def fake_post(
        url,
        auth,
        json,
        timeout,
    ):
        assert json["quantity"] == -2

        return FakeResponse(
            {
                "id": 987655,
                "ticker": "AAPL_US_EQ",
                "quantity": -2,
                "side": "SELL",
                "status": "NEW",
                "type": "MARKET",
                "filledQuantity": 0,
                "filledValue": 0,
                "currency": "GBP",
            }
        )

    monkeypatch.setattr(
        httpx,
        "post",
        fake_post,
    )

    client = Trading212Client(
        api_key="key",
        api_secret="secret",
        environment="DEMO",
    )

    result = client.place_market_order(
        ticker="AAPL_US_EQ",
        quantity=-2,
    )

    assert result.side == "SELL"
    assert result.quantity == -2


def test_market_order_rejects_live_environment() -> None:
    client = Trading212Client(
        api_key="key",
        api_secret="secret",
        environment="LIVE",
    )

    with pytest.raises(
        BrokerError,
        match="DEMO",
    ):
        client.place_market_order(
            ticker="AAPL_US_EQ",
            quantity=1,
        )


def test_market_order_rejects_zero_quantity() -> None:
    client = Trading212Client(
        api_key="key",
        api_secret="secret",
        environment="DEMO",
    )

    with pytest.raises(
        ValueError,
        match="cannot be zero",
    ):
        client.place_market_order(
            ticker="AAPL_US_EQ",
            quantity=0,
        )


def test_market_order_rejects_invalid_response(
    monkeypatch,
) -> None:
    def fake_post(
        url,
        auth,
        json,
        timeout,
    ):
        return FakeResponse(
            {
                "unexpected": "response"
            }
        )

    monkeypatch.setattr(
        httpx,
        "post",
        fake_post,
    )

    client = Trading212Client(
        api_key="key",
        api_secret="secret",
        environment="DEMO",
    )

    with pytest.raises(
        BrokerError,
        match="invalid market-order response",
    ):
        client.place_market_order(
            ticker="AAPL_US_EQ",
            quantity=1,
        )

def test_market_order_http_error_includes_response(
    monkeypatch,
) -> None:
    request = httpx.Request(
        "POST",
        (
            "https://demo.trading212.com/"
            "api/v0/equity/orders/market"
        ),
    )

    response = httpx.Response(
        403,
        request=request,
        json={
            "error": (
                "API key does not have order "
                "permissions."
            ),
        },
    )

    def fake_post(
        url,
        auth,
        json,
        timeout,
    ):
        return response

    monkeypatch.setattr(
        httpx,
        "post",
        fake_post,
    )

    client = Trading212Client(
        api_key="key",
        api_secret="secret",
        environment="DEMO",
    )

    with pytest.raises(
        BrokerError,
        match=(
            "API key does not have order "
            "permissions"
        ),
    ):
        client.place_market_order(
            ticker="AAPL_US_EQ",
            quantity=1,
        )

def test_get_pending_order(
    monkeypatch,
) -> None:
    captured_url = ""

    def fake_get(
        url,
        auth,
        timeout,
    ):
        nonlocal captured_url
        captured_url = url

        return FakeResponse(
            {
                "id": 987654,
                "currency": "GBP",
                "instrument": {
                    "ticker": "AAPL_US_EQ",
                },
                "quantity": 2,
                "side": "BUY",
                "status": "PARTIALLY_FILLED",
                "type": "MARKET",
                "filledQuantity": 1,
                "filledValue": 150,
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

    result = client.get_pending_order(
        order_id=987654
    )

    assert captured_url.endswith(
        "/equity/orders/987654"
    )

    assert result.order_id == 987654
    assert result.ticker == "AAPL_US_EQ"
    assert result.status == "PARTIALLY_FILLED"
    assert result.filled_quantity == 1
    assert result.filled_value == 150


def test_get_pending_order_rejects_invalid_id() -> None:
    client = Trading212Client(
        api_key="key",
        api_secret="secret",
        environment="DEMO",
    )

    with pytest.raises(
        ValueError,
        match="Order ID must be positive",
    ):
        client.get_pending_order(
            order_id=0
        )


def test_get_pending_order_rejects_invalid_response(
    monkeypatch,
) -> None:
    def fake_get(
        url,
        auth,
        timeout,
    ):
        return FakeResponse(
            {
                "unexpected": "response",
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

    with pytest.raises(
        BrokerError,
        match="invalid pending-order response",
    ):
        client.get_pending_order(
            order_id=987654
        )


def test_shared_order_parser_accepts_top_level_ticker() -> None:
    result = Trading212Client._parse_order_result(
        data={
            "id": 1,
            "ticker": "AAPL_US_EQ",
            "quantity": 1,
            "side": "BUY",
            "status": "NEW",
            "type": "MARKET",
            "filledQuantity": 0,
            "filledValue": 0,
            "currency": "GBP",
        },
        error_message="Invalid order.",
    )

    assert result.ticker == "AAPL_US_EQ"
    assert result.status == "NEW"


def test_shared_order_parser_accepts_instrument_ticker() -> None:
    result = Trading212Client._parse_order_result(
        data={
            "id": 1,
            "instrument": {
                "ticker": "AAPL_US_EQ",
            },
            "quantity": 1,
            "side": "BUY",
            "status": "FILLED",
            "type": "MARKET",
            "filledQuantity": 1,
            "filledValue": 150,
            "currency": "GBP",
        },
        error_message="Invalid order.",
    )

    assert result.ticker == "AAPL_US_EQ"
    assert result.status == "FILLED"
    assert result.filled_quantity == 1

def historical_order_data(
    order_id: int,
    status: str = "FILLED",
) -> dict[str, object]:
    return {
        "id": order_id,
        "ticker": "AAPL_US_EQ",
        "quantity": 2,
        "side": "BUY",
        "status": status,
        "type": "MARKET",
        "filledQuantity": 2,
        "filledValue": 300,
        "currency": "GBP",
    }


def test_find_historical_order_on_first_page(
    monkeypatch,
) -> None:
    requested_urls: list[str] = []

    def fake_get(
        url,
        auth,
        timeout,
    ):
        requested_urls.append(url)

        return FakeResponse(
            {
                "items": [
                    historical_order_data(
                        order_id=987654
                    )
                ],
                "nextPagePath": None,
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

    result = client.find_historical_order(
        order_id=987654
    )

    assert result is not None
    assert result.order_id == 987654
    assert result.status == "FILLED"

    assert requested_urls[0].endswith(
        "/equity/history/orders?limit=50"
    )


def test_find_historical_order_follows_next_page(
    monkeypatch,
) -> None:
    requested_urls: list[str] = []

    def fake_get(
        url,
        auth,
        timeout,
    ):
        requested_urls.append(url)

        if len(requested_urls) == 1:
            return FakeResponse(
                {
                    "items": [
                        historical_order_data(
                            order_id=111
                        )
                    ],
                    "nextPagePath": (
                        "/api/v0/equity/history/"
                        "orders?limit=50&cursor=123"
                    ),
                }
            )

        return FakeResponse(
            {
                "items": [
                    historical_order_data(
                        order_id=987654
                    )
                ],
                "nextPagePath": None,
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

    result = client.find_historical_order(
        order_id=987654
    )

    assert result is not None
    assert result.order_id == 987654
    assert len(requested_urls) == 2

    assert requested_urls[1].endswith(
        "/equity/history/"
        "orders?limit=50&cursor=123"
    )

    assert "/api/v0/api/v0/" not in (
        requested_urls[1]
    )


def test_find_historical_order_returns_none_when_missing(
    monkeypatch,
) -> None:
    def fake_get(
        url,
        auth,
        timeout,
    ):
        return FakeResponse(
            {
                "items": [
                    historical_order_data(
                        order_id=111
                    )
                ],
                "nextPagePath": None,
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

    result = client.find_historical_order(
        order_id=987654
    )

    assert result is None


def test_find_historical_order_respects_max_pages(
    monkeypatch,
) -> None:
    request_count = 0

    def fake_get(
        url,
        auth,
        timeout,
    ):
        nonlocal request_count
        request_count += 1

        return FakeResponse(
            {
                "items": [],
                "nextPagePath": (
                    "/api/v0/equity/history/"
                    f"orders?limit=50&cursor="
                    f"{request_count}"
                ),
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

    result = client.find_historical_order(
        order_id=987654,
        max_pages=2,
    )

    assert result is None
    assert request_count == 2


def test_find_historical_order_rejects_invalid_id() -> None:
    client = Trading212Client(
        api_key="key",
        api_secret="secret",
    )

    with pytest.raises(
        ValueError,
        match="Order ID must be positive",
    ):
        client.find_historical_order(
            order_id=0
        )


def test_find_historical_order_rejects_invalid_page_limit() -> None:
    client = Trading212Client(
        api_key="key",
        api_secret="secret",
    )

    with pytest.raises(
        ValueError,
        match="Maximum pages",
    ):
        client.find_historical_order(
            order_id=1,
            max_pages=0,
        )


def test_find_historical_order_rejects_invalid_response(
    monkeypatch,
) -> None:
    def fake_get(
        url,
        auth,
        timeout,
    ):
        return FakeResponse(
            {
                "unexpected": "response",
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
        match="historical-orders response",
    ):
        client.find_historical_order(
            order_id=987654
        )

def test_get_pending_order_raises_not_found_error(
    monkeypatch,
) -> None:
    def fake_get(
        url,
        auth,
        timeout,
    ):
        return FakeResponse(
            {},
            status_code=404,
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

    with pytest.raises(
        BrokerResourceNotFoundError,
        match="resource was not found",
    ):
        client.get_pending_order(
            order_id=987654
        )


def test_non_404_get_error_remains_generic_broker_error(
    monkeypatch,
) -> None:
    def fake_get(
        url,
        auth,
        timeout,
    ):
        return FakeResponse(
            {},
            status_code=500,
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

    with pytest.raises(
        BrokerError,
        match="HTTP 500",
    ) as error_info:
        client.get_pending_order(
            order_id=987654
        )

    assert not isinstance(
        error_info.value,
        BrokerResourceNotFoundError,
    )