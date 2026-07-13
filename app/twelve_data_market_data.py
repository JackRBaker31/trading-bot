import logging
from datetime import datetime, timezone

import httpx

from app.market_data import (
    MarketDataError,
    MarketDataProvider,
    PriceQuote,
)


logger = logging.getLogger(__name__)


class TwelveDataMarketDataProvider(MarketDataProvider):
    BASE_URL = "https://api.twelvedata.com/quote"

    def __init__(
        self,
        api_key: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        cleaned_api_key = api_key.strip()

        if not cleaned_api_key:
            raise ValueError(
                "A Twelve Data API key is required."
            )

        if timeout_seconds <= 0:
            raise ValueError(
                "Timeout must be greater than zero."
            )

        self.api_key = cleaned_api_key
        self.timeout_seconds = timeout_seconds

    def get_price(self, symbol: str) -> PriceQuote:
        cleaned_symbol = symbol.upper().strip()

        if not cleaned_symbol:
            raise ValueError(
                "A stock symbol is required."
            )

        logger.info(
            "market_data_request provider=TWELVE_DATA symbol=%s",
            cleaned_symbol,
        )

        try:
            response = httpx.get(
                self.BASE_URL,
                params={
                    "symbol": cleaned_symbol,
                    "apikey": self.api_key,
                },
                timeout=self.timeout_seconds,
            )

            response.raise_for_status()

        except httpx.TimeoutException as error:
            logger.error(
                "market_data_timeout provider=TWELVE_DATA symbol=%s",
                cleaned_symbol,
            )

            raise MarketDataError(
                f"Market-data request timed out for "
                f"{cleaned_symbol}."
            ) from error

        except httpx.HTTPError as error:
            logger.exception(
                "market_data_http_error "
                "provider=TWELVE_DATA symbol=%s",
                cleaned_symbol,
            )

            raise MarketDataError(
                f"Market-data request failed for "
                f"{cleaned_symbol}."
            ) from error

        try:
            data = response.json()
        except ValueError as error:
            raise MarketDataError(
                "Twelve Data returned invalid JSON."
            ) from error

        if not isinstance(data, dict):
            raise MarketDataError(
                "Twelve Data returned an invalid response."
            )

        if data.get("status") == "error":
            message = str(
                data.get(
                    "message",
                    "Unknown Twelve Data error.",
                )
            )

            logger.warning(
                "market_data_provider_error "
                "provider=TWELVE_DATA symbol=%s message=%s",
                cleaned_symbol,
                message,
            )

            raise MarketDataError(message)

        raw_price = data.get("close")

        if raw_price is None:
            raise MarketDataError(
                f"No closing price was returned for "
                f"{cleaned_symbol}."
            )

        try:
            price = float(raw_price)
        except (TypeError, ValueError) as error:
            raise MarketDataError(
                f"Invalid price returned for "
                f"{cleaned_symbol}: {raw_price}"
            ) from error

        if price <= 0:
            raise MarketDataError(
                f"Non-positive price returned for "
                f"{cleaned_symbol}: {price}"
            )

        quote = PriceQuote(
            symbol=cleaned_symbol,
            price=price,
            timestamp=datetime.now(timezone.utc),
            provider="TWELVE_DATA",
        )

        logger.info(
            "market_data_received "
            "provider=TWELVE_DATA symbol=%s price=%.4f",
            quote.symbol,
            quote.price,
        )

        return quote