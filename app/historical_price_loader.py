from app.historical_data import HistoricalPrice
from app.twelve_data_historical_data import (
    TwelveDataHistoricalDataClient,
)


class HistoricalPriceLoader:
    def __init__(
        self,
        *,
        client: TwelveDataHistoricalDataClient,
    ) -> None:
        self.client = client

    def load_daily_prices(
        self,
        *,
        symbols: list[str],
        output_size: int,
    ) -> list[HistoricalPrice]:
        cleaned_symbols = [
            symbol.upper().strip()
            for symbol in symbols
        ]

        if not cleaned_symbols:
            raise ValueError(
                "At least one symbol is required."
            )

        if any(
            not symbol
            for symbol in cleaned_symbols
        ):
            raise ValueError(
                "Symbols cannot be empty."
            )

        if len(set(cleaned_symbols)) != len(
            cleaned_symbols
        ):
            raise ValueError(
                "Symbols must be unique."
            )

        close_prices_by_symbol = {}

        for symbol in cleaned_symbols:
            bars = self.client.get_daily_bars(
                symbol=symbol,
                output_size=output_size,
            )

            close_prices_by_symbol[symbol] = {
                bar.trading_date: bar.close_price
                for bar in bars
            }

        shared_dates = set.intersection(
            *(
                set(prices_by_date)
                for prices_by_date
                in close_prices_by_symbol.values()
            )
        )

        if not shared_dates:
            raise ValueError(
                "No shared historical dates were found."
            )

        return [
            HistoricalPrice(
                trading_date=trading_date,
                prices={
                    symbol: close_prices_by_symbol[
                        symbol
                    ][trading_date]
                    for symbol in cleaned_symbols
                },
            )
            for trading_date in sorted(
                shared_dates
            )
        ]