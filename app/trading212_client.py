import json
import logging

import httpx

from app.broker import (
    BrokerAccountSummary,
    BrokerClient,
    BrokerError,
    BrokerOrderRejectedError,
    BrokerOrderResult,
    BrokerOrderSubmissionUnknownError,
    BrokerPosition,
    BrokerResourceNotFoundError,
)


logger = logging.getLogger(__name__)


class Trading212Client(BrokerClient):
    DEMO_BASE_URL = (
        "https://demo.trading212.com/api/v0"
    )

    LIVE_BASE_URL = (
        "https://live.trading212.com/api/v0"
    )

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        environment: str = "DEMO",
        timeout_seconds: float = 10.0,
    ) -> None:
        cleaned_key = api_key.strip()
        cleaned_secret = api_secret.strip()
        cleaned_environment = (
            environment.upper().strip()
        )

        if not cleaned_key:
            raise ValueError(
                "Trading 212 API key is required."
            )

        if not cleaned_secret:
            raise ValueError(
                "Trading 212 API secret is required."
            )

        if cleaned_environment not in {
            "DEMO",
            "LIVE",
        }:
            raise ValueError(
                "Trading 212 environment must be "
                "DEMO or LIVE."
            )

        if timeout_seconds <= 0:
            raise ValueError(
                "Timeout must be positive."
            )

        self.api_key = cleaned_key
        self.api_secret = cleaned_secret
        self.environment = cleaned_environment
        self.timeout_seconds = timeout_seconds

        if self.environment == "DEMO":
            self.base_url = self.DEMO_BASE_URL
        else:
            self.base_url = self.LIVE_BASE_URL

    def get_account_summary(
        self,
    ) -> BrokerAccountSummary:
        data = self._get(
            "/equity/account/summary"
        )

        if not isinstance(data, dict):
            raise BrokerError(
                "Trading 212 returned an invalid "
                "account summary."
            )

        try:
            cash = data["cash"]
            investments = data["investments"]

            if not isinstance(cash, dict):
                raise TypeError(
                    "Cash must be an object."
                )

            if not isinstance(investments, dict):
                raise TypeError(
                    "Investments must be an object."
                )

            return BrokerAccountSummary(
                account_id=int(data["id"]),
                currency=str(data["currency"]),
                available_to_trade=float(
                    cash["availableToTrade"]
                ),
                reserved_for_orders=float(
                    cash["reservedForOrders"]
                ),
                cash_in_pies=float(
                    cash["inPies"]
                ),
                investments_current_value=float(
                    investments["currentValue"]
                ),
                investments_total_cost=float(
                    investments["totalCost"]
                ),
                realized_profit_loss=float(
                    investments["realizedProfitLoss"]
                ),
                unrealized_profit_loss=float(
                    investments["unrealizedProfitLoss"]
                ),
                total_value=float(
                    data["totalValue"]
                ),
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            raise BrokerError(
                "Trading 212 returned an invalid "
                "account summary."
            ) from error

    def get_positions(
        self,
    ) -> list[BrokerPosition]:
        data = self._get(
            "/equity/positions"
        )

        if not isinstance(data, list):
            raise BrokerError(
                "Trading 212 returned an invalid "
                "positions response."
            )

        positions: list[BrokerPosition] = []

        for item in data:
            if not isinstance(item, dict):
                raise BrokerError(
                    "Trading 212 returned an invalid "
                    "position."
                )

            try:
                instrument = item["instrument"]

                if not isinstance(
                    instrument,
                    dict,
                ):
                    raise TypeError(
                        "Instrument must be an object."
                    )

                ticker = str(
                    instrument["ticker"]
                )

                quantity = float(
                    item["quantity"]
                )

                average_price_paid = float(
                    item["averagePricePaid"]
                )

                current_price = float(
                    item["currentPrice"]
                )

                profit_loss = float(
                    item.get(
                        "profitLoss",
                        (
                            current_price
                            - average_price_paid
                        )
                        * quantity,
                    )
                )

                positions.append(
                    BrokerPosition(
                        ticker=ticker,
                        quantity=quantity,
                        average_price_paid=(
                            average_price_paid
                        ),
                        current_price=current_price,
                        profit_loss=profit_loss,
                    )
                )
            except (
                KeyError,
                TypeError,
                ValueError,
            ) as error:
                raise BrokerError(
                    "Trading 212 returned an invalid "
                    "position."
                ) from error

        return positions

    def place_market_order(
        self,
        ticker: str,
        quantity: float,
        extended_hours: bool = False,
    ) -> BrokerOrderResult:
        cleaned_ticker = ticker.upper().strip()

        if self.environment != "DEMO":
            raise BrokerError(
                "Market orders are currently restricted "
                "to the DEMO environment."
            )

        if not cleaned_ticker:
            raise ValueError(
                "A broker ticker is required."
            )

        if quantity == 0:
            raise ValueError(
                "Order quantity cannot be zero."
            )

        data = self._post(
            path="/equity/orders/market",
            payload={
                "ticker": cleaned_ticker,
                "quantity": quantity,
                "extendedHours": extended_hours,
            },
        )

        return self._parse_order_result(
            data=data,
            error_message=(
                "Trading 212 returned an invalid "
                "market-order response."
            ),
        )

    def get_pending_order(
        self,
        order_id: int,
    ) -> BrokerOrderResult:
        if order_id <= 0:
            raise ValueError(
                "Order ID must be positive."
            )

        data = self._get(
            f"/equity/orders/{order_id}"
        )

        return self._parse_order_result(
            data=data,
            error_message=(
                "Trading 212 returned an invalid "
                "pending-order response."
            ),
        )

    def find_historical_order(
        self,
        order_id: int,
        max_pages: int = 5,
    ) -> BrokerOrderResult | None:
        if order_id <= 0:
            raise ValueError(
                "Order ID must be positive."
            )

        if max_pages <= 0:
            raise ValueError(
                "Maximum pages must be positive."
            )

        path = "/equity/history/orders?limit=50"

        for _ in range(max_pages):
            data = self._get(path)

            if not isinstance(data, dict):
                raise BrokerError(
                    "Trading 212 returned an invalid "
                    "historical-orders response."
                )

            items = data.get("items")

            if not isinstance(items, list):
                raise BrokerError(
                    "Trading 212 returned an invalid "
                    "historical-orders response."
                )

            for item in items:
                if not isinstance(item, dict):
                    raise BrokerError(
                        "Trading 212 returned an invalid "
                        "historical order."
                    )

                try:
                    item_order_id = int(
                        item["id"]
                    )
                except (
                    KeyError,
                    TypeError,
                    ValueError,
                ) as error:
                    raise BrokerError(
                        "Trading 212 returned an invalid "
                        "historical order."
                    ) from error

                if item_order_id == order_id:
                    return self._parse_order_result(
                        data=item,
                        error_message=(
                            "Trading 212 returned an "
                            "invalid historical order."
                        ),
                    )

            next_page_path = data.get(
                "nextPagePath"
            )

            if next_page_path is None:
                return None

            if not isinstance(
                next_page_path,
                str,
            ):
                raise BrokerError(
                    "Trading 212 returned an invalid "
                    "historical-orders page path."
                )

            path = self._normalise_api_path(
                next_page_path
            )

        return None

    @staticmethod
    def _parse_order_result(
        data: object,
        error_message: str,
    ) -> BrokerOrderResult:
        if not isinstance(data, dict):
            raise BrokerError(
                error_message
            )

        try:
            raw_ticker = data.get("ticker")

            if raw_ticker is None:
                instrument = data["instrument"]

                if not isinstance(
                    instrument,
                    dict,
                ):
                    raise TypeError(
                        "Instrument must be an object."
                    )

                raw_ticker = instrument["ticker"]

            return BrokerOrderResult(
                order_id=int(data["id"]),
                ticker=str(raw_ticker),
                quantity=float(data["quantity"]),
                side=str(data["side"]),
                status=str(data["status"]),
                order_type=str(data["type"]),
                filled_quantity=float(
                    data.get(
                        "filledQuantity",
                        0,
                    )
                ),
                filled_value=float(
                    data.get(
                        "filledValue",
                        0,
                    )
                ),
                currency=str(data["currency"]),
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            raise BrokerError(
                error_message
            ) from error

    @staticmethod
    def _normalise_api_path(
        path: str,
    ) -> str:
        cleaned_path = path.strip()

        api_prefix = "/api/v0"

        if cleaned_path.startswith(
            api_prefix
        ):
            cleaned_path = cleaned_path[
                len(api_prefix):
            ]

        if not cleaned_path.startswith("/"):
            cleaned_path = (
                "/" + cleaned_path
            )

        return cleaned_path

    def _get(
        self,
        path: str,
    ) -> object:
        url = f"{self.base_url}{path}"

        logger.info(
            "broker_request environment=%s "
            "method=GET path=%s",
            self.environment,
            path,
        )

        try:
            response = httpx.get(
                url,
                auth=httpx.BasicAuth(
                    self.api_key,
                    self.api_secret,
                ),
                timeout=self.timeout_seconds,
            )

            response.raise_for_status()

        except httpx.TimeoutException as error:
            logger.error(
                "broker_order_timeout "
                "environment=%s path=%s",
                self.environment,
                path,
            )

            raise BrokerOrderSubmissionUnknownError(
                "Trading 212 order request timed out. "
                "Order status must be checked before "
                "retrying."
            ) from error

        except httpx.HTTPStatusError as error:
            status_code = (
                error.response.status_code
            )

            logger.error(
                "broker_http_error "
                "environment=%s path=%s "
                "status_code=%s",
                self.environment,
                path,
                status_code,
            )

            if status_code == 429:
                reset_at = (
                    error.response.headers.get(
                        "x-ratelimit-reset",
                        "unknown",
                    )
                )

                remaining = (
                    error.response.headers.get(
                        "x-ratelimit-remaining",
                        "0",
                    )
                )

                raise BrokerError(
                    "Trading 212 rate limit reached. "
                    f"Remaining requests: {remaining}. "
                    f"Reset time: {reset_at}."
                ) from error

            if status_code == 404:
                raise BrokerResourceNotFoundError(
                    f"Trading 212 resource was not found: "
                    f"{path}"
                ) from error

            raise BrokerError(
                f"Trading 212 returned HTTP "
                f"{status_code}."
            ) from error

        except httpx.HTTPError as error:
            logger.exception(
                "broker_connection_error "
                "environment=%s path=%s",
                self.environment,
                path,
            )

            raise BrokerError(
                "Trading 212 connection failed."
            ) from error

        try:
            return response.json()
        except ValueError as error:
            raise BrokerError(
                "Trading 212 returned invalid JSON."
            ) from error

    @staticmethod
    def _format_error_response(
        response: httpx.Response,
    ) -> str:
        try:
            data = response.json()
        except ValueError:
            detail = response.text
        else:
            detail = ""

            if isinstance(data, dict):
                for key in (
                    "message",
                    "error",
                    "detail",
                ):
                    value = data.get(key)

                    if isinstance(value, str):
                        detail = value
                        break

                if not detail:
                    detail = json.dumps(
                        data,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    )
            elif isinstance(data, list):
                detail = json.dumps(
                    data,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
            else:
                detail = str(data)

        cleaned_detail = " ".join(
            detail.split()
        )

        if not cleaned_detail:
            return "No response details provided."

        return cleaned_detail[:500]

    def _post(
        self,
        path: str,
        payload: dict[str, object],
    ) -> object:
        url = f"{self.base_url}{path}"

        logger.warning(
            "broker_order_request environment=%s "
            "method=POST path=%s payload=%s",
            self.environment,
            path,
            payload,
        )

        try:
            response = httpx.post(
                url,
                auth=httpx.BasicAuth(
                    self.api_key,
                    self.api_secret,
                ),
                json=payload,
                timeout=self.timeout_seconds,
            )

            response.raise_for_status()

        except httpx.TimeoutException as error:
            logger.error(
                "broker_order_timeout "
                "environment=%s path=%s",
                self.environment,
                path,
            )

            raise BrokerOrderSubmissionUnknownError(
                "Trading 212 order request timed out. "
                "Order status must be checked before "
                "retrying."
            ) from error

        except httpx.HTTPStatusError as error:
            status_code = (
                error.response.status_code
            )

            response_detail = (
                self._format_error_response(
                    error.response
                )
            )

            logger.error(
                "broker_order_http_error "
                "environment=%s path=%s "
                "status_code=%s detail=%s",
                self.environment,
                path,
                status_code,
                response_detail,
            )

            if status_code == 429:
                reset_at = (
                    error.response.headers.get(
                        "x-ratelimit-reset",
                        "unknown",
                    )
                )

                raise BrokerError(
                    "Trading 212 order rate limit "
                    "reached. "
                    f"Reset time: {reset_at}. "
                    "Do not retry until the order "
                    "status has been checked. "
                    "Broker response: "
                    f"{response_detail}"
                ) from error

            raise BrokerOrderRejectedError(
                f"Trading 212 returned HTTP "
                f"{status_code} for the order request. "
                "Broker response: "
                f"{response_detail}"
            ) from error

        except httpx.HTTPError as error:
            logger.exception(
                "broker_order_connection_error "
                "environment=%s path=%s",
                self.environment,
                path,
            )

            raise BrokerOrderSubmissionUnknownError(
                "Trading 212 order connection failed. "
                "Order status must be checked before "
                "retrying."
            ) from error

        try:
            return response.json()
        except ValueError as error:
            raise BrokerOrderSubmissionUnknownError(
                "Trading 212 returned invalid JSON "
                "for the market order. Order status "
                "must be checked before retrying."
            ) from error