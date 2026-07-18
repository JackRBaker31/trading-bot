import csv
import os
from dotenv import load_dotenv
from pathlib import Path

from app.config import load_config
from app.historical_price_loader import (
    HistoricalPriceLoader,
)
from app.twelve_data_historical_data import (
    TwelveDataHistoricalDataClient,
)


OUTPUT_PATH = Path(
    "data/research_prices.csv"
)


def main() -> None:
    load_dotenv()

    config = load_config()

    api_key = os.getenv(
        "TWELVE_DATA_API_KEY"
    )

    if api_key is None or not api_key.strip():
        raise RuntimeError(
            "TWELVE_DATA_API_KEY was not found "
            "in the environment."
        )

    client = TwelveDataHistoricalDataClient(
        api_key=api_key,
        max_attempts=2,
    )

    loader = HistoricalPriceLoader(
        client=client,
    )

    historical_prices = (
        loader.load_daily_prices(
            symbols=config.symbols,
            output_size=500,
        )
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        mode="w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "date",
                *config.symbols,
            ]
        )

        for price_point in historical_prices:
            writer.writerow(
                [
                    price_point
                    .trading_date
                    .isoformat(),
                    *[
                        price_point.prices[
                            symbol
                        ]
                        for symbol in config.symbols
                    ],
                ]
            )

    print(
        f"Saved {len(historical_prices)} "
        f"shared rows to {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()