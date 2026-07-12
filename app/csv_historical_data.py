import csv
from datetime import date
from pathlib import Path

from app.historical_data import HistoricalPrice


class HistoricalDataError(Exception):
    """Raised when historical CSV data is invalid."""


def load_historical_prices_from_csv(
    file_path: str,
) -> list[HistoricalPrice]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Historical data file does not exist: {path}"
        )

    with path.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise HistoricalDataError(
                "Historical CSV file has no header."
            )

        cleaned_headers = [
            header.strip()
            for header in reader.fieldnames
            if header is not None
        ]

        if "date" not in cleaned_headers:
            raise HistoricalDataError(
                "Historical CSV must contain a 'date' column."
            )

        symbols = [
            header.upper()
            for header in cleaned_headers
            if header != "date"
        ]

        expected_symbols = set(symbols)

        if not symbols:
            raise HistoricalDataError(
                "Historical CSV must contain at least one symbol."
            )

        historical_prices: list[HistoricalPrice] = []
        seen_dates: set[date] = set()

        for row_number, raw_row in enumerate(
            reader,
            start=2,
        ):
            row = {
                str(key).strip(): (
                    value.strip()
                    if value is not None
                    else ""
                )
                for key, value in raw_row.items()
                if key is not None
            }

            raw_date = row.get("date", "")

            if not raw_date:
                raise HistoricalDataError(
                    f"Missing date on row {row_number}."
                )

            try:
                trading_date = date.fromisoformat(
                    raw_date
                )
            except ValueError as error:
                raise HistoricalDataError(
                    f"Invalid date '{raw_date}' "
                    f"on row {row_number}. "
                    "Dates must use YYYY-MM-DD."
                ) from error

            if trading_date in seen_dates:
                raise HistoricalDataError(
                    f"Duplicate date found: "
                    f"{trading_date.isoformat()}."
                )

            prices: dict[str, float] = {}

            for original_header in cleaned_headers:
                if original_header == "date":
                    continue

                symbol = original_header.upper()
                raw_price = row.get(
                    original_header,
                    "",
                )

                if not raw_price:
                    raise HistoricalDataError(
                        f"Missing price for {symbol} "
                        f"on row {row_number}."
                    )

                try:
                    price = float(raw_price)
                except ValueError as error:
                    raise HistoricalDataError(
                        f"Invalid price '{raw_price}' "
                        f"for {symbol} on row "
                        f"{row_number}."
                    ) from error

                if price <= 0:
                    raise HistoricalDataError(
                        f"Price for {symbol} on row "
                        f"{row_number} must be positive."
                    )

                prices[symbol] = price

            historical_prices.append(
                HistoricalPrice(
                    trading_date=trading_date,
                    prices=prices,
                )
            )

            seen_dates.add(trading_date)

    if not historical_prices:
        raise HistoricalDataError(
            "Historical CSV contains no data rows."
        )

    historical_prices.sort(
        key=lambda item: item.trading_date
    )

    return historical_prices