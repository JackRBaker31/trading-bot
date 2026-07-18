from datetime import date
import logging

import httpx

from app.backtest_models import HistoricalPriceBar
from app.market_data import MarketDataError


logger = logging.getLogger(__name__)


class TwelveDataHistoricalDataClient:
    BASE_URL = (
        "https://api.twelvedata.com/time_series"
    )

    def __init__(
        self,
        *,
        api_key: str,
        timeout_seconds: float = 10.0,
        max_attempts: int = 1,
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

        if max_attempts <= 0:
            raise ValueError(
                "Maximum attempts must be greater than zero."
            )

        self.api_key = cleaned_api_key
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts

    def get_daily_bars(
        self,
        *,
        symbol: str,
        output_size: int,
    ) -> list[HistoricalPriceBar]:
        cleaned_symbol = symbol.upper().strip()

        if not cleaned_symbol:
            raise ValueError(
                "A stock symbol is required."
            )

        if output_size <= 0:
            raise ValueError(
                "Output size must be positive."
            )

        response: httpx.Response | None = None

        for attempt_number in range(
            1,
            self.max_attempts + 1,
        ):
            try:
                response = httpx.get(
                    self.BASE_URL,
                    params={
                        "symbol": cleaned_symbol,
                        "interval": "1day",
                        "outputsize": output_size,
                        "apikey": self.api_key,
                    },
                    timeout=self.timeout_seconds,
                )

                response.raise_for_status()
                break

            except httpx.TimeoutException as error:
                logger.warning(
                    "historical_data_timeout "
                    "provider=TWELVE_DATA symbol=%s "
                    "attempt=%s max_attempts=%s",
                    cleaned_symbol,
                    attempt_number,
                    self.max_attempts,
                )

                if attempt_number == self.max_attempts:
                    raise MarketDataError(
                        "Historical-data request timed out "
                        f"for {cleaned_symbol}."
                    ) from error

            except httpx.HTTPError as error:
                raise MarketDataError(
                    "Historical-data request failed "
                    f"for {cleaned_symbol}."
                ) from error

        if response is None:
            raise MarketDataError(
                "Historical-data request failed "
                f"for {cleaned_symbol}."
            )

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
            raise MarketDataError(
                str(
                    data.get(
                        "message",
                        "Unknown Twelve Data error.",
                    )
                )
            )

        values = data.get("values")

        if not isinstance(values, list):
            raise MarketDataError(
                "Twelve Data returned invalid historical values."
            )

        bars = [
            self._parse_bar(
                symbol=cleaned_symbol,
                raw_value=raw_value,
            )
            for raw_value in values
        ]

        bars.sort(
            key=lambda bar: bar.trading_date
        )

        return bars

    @staticmethod
    def _parse_bar(
        *,
        symbol: str,
        raw_value: object,
    ) -> HistoricalPriceBar:
        if not isinstance(raw_value, dict):
            raise MarketDataError(
                "Twelve Data returned an invalid historical bar."
            )

        try:
            trading_date = date.fromisoformat(
                str(raw_value["datetime"])[:10]
            )

            return HistoricalPriceBar(
                symbol=symbol,
                trading_date=trading_date,
                open_price=float(raw_value["open"]),
                high_price=float(raw_value["high"]),
                low_price=float(raw_value["low"]),
                close_price=float(raw_value["close"]),
                volume=int(raw_value["volume"]),
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            raise MarketDataError(
                "Twelve Data returned an invalid historical bar."
            ) from error