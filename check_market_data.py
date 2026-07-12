import os

from dotenv import load_dotenv

from app.logging_config import setup_logging
from app.twelve_data_market_data import (
    TwelveDataMarketDataProvider,
)


def main() -> None:
    setup_logging()
    load_dotenv()

    api_key = os.getenv("TWELVE_DATA_API_KEY")

    if api_key is None:
        raise RuntimeError(
            "TWELVE_DATA_API_KEY was not found in .env."
        )

    provider = TwelveDataMarketDataProvider(
        api_key=api_key
    )

    quote = provider.get_price("AAPL")

    print("\nRead-only market-data connection successful.")
    print(f"Provider: {quote.provider}")
    print(f"Symbol: {quote.symbol}")
    print(f"Latest available price: ${quote.price:.2f}")
    print(f"Retrieved at: {quote.timestamp}")
    print("No order was created.")
    print("No broker was contacted.")


if __name__ == "__main__":
    main()