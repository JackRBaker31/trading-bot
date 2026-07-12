import logging

import httpx

from app.broker import (
    BrokerAccountSummary,
    BrokerClient,
    BrokerError,
    BrokerPosition,
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

        try:
            cash = data["cash"]
            investments = data["investments"]

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
            try:
                instrument = item["instrument"]

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
                "broker_timeout environment=%s "
                "path=%s",
                self.environment,
                path,
            )

            raise BrokerError(
                "Trading 212 request timed out."
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