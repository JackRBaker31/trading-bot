from app.broker import BrokerInstrument


class InstrumentResolver:
    def __init__(
        self,
        instruments: list[BrokerInstrument],
    ) -> None:
        self.instruments = instruments

    def resolve_symbols(
        self,
        symbols: list[str],
    ) -> dict[str, str]:
        tickers_by_symbol: dict[
            str,
            list[str],
        ] = {}

        for instrument in self.instruments:
            symbol = instrument.ticker.split(
                "_",
                maxsplit=1,
            )[0].upper()

            tickers_by_symbol.setdefault(
                symbol,
                [],
            ).append(
                instrument.ticker
            )

        mapping: dict[str, str] = {}

        for symbol in symbols:
            cleaned_symbol = symbol.upper().strip()

            if not cleaned_symbol:
                raise ValueError(
                    "Configured symbols cannot be empty."
                )

            matching_tickers = (
                tickers_by_symbol.get(
                    cleaned_symbol,
                    [],
                )
            )

            if not matching_tickers:
                raise ValueError(
                    f"No Trading 212 instrument was "
                    f"found for {cleaned_symbol}."
                )

            if len(matching_tickers) > 1:
                raise ValueError(
                    f"Trading 212 instrument mapping "
                    f"is ambiguous for "
                    f"{cleaned_symbol}."
                )

            mapping[cleaned_symbol] = (
                matching_tickers[0]
            )

        return mapping