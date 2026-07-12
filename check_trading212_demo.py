import os

from dotenv import load_dotenv

from app.logging_config import setup_logging
from app.trading212_client import (
    Trading212Client,
)


def main() -> None:
    setup_logging()
    load_dotenv()

    api_key = os.getenv(
        "TRADING212_DEMO_API_KEY"
    )

    api_secret = os.getenv(
        "TRADING212_DEMO_API_SECRET"
    )

    if api_key is None:
        raise RuntimeError(
            "TRADING212_DEMO_API_KEY was not "
            "found in .env."
        )

    if api_secret is None:
        raise RuntimeError(
            "TRADING212_DEMO_API_SECRET was not "
            "found in .env."
        )

    client = Trading212Client(
        api_key=api_key,
        api_secret=api_secret,
        environment="DEMO",
    )

    summary = client.get_account_summary()
    positions = client.get_positions()

    print("\nTrading 212 demo connection successful.")
    print("Read-only mode.")
    print(
        f"Account ID: {summary.account_id}"
    )
    print(
        f"Currency: {summary.currency}"
    )
    print(
        f"Available to trade: "
        f"{summary.available_to_trade:.2f}"
    )
    print(
        f"Total account value: "
        f"{summary.total_value:.2f}"
    )
    print(
        f"Open positions: {len(positions)}"
    )

    for position in positions:
        print(
            f"{position.ticker}: "
            f"{position.quantity} shares, "
            f"current price "
            f"{position.current_price:.2f}, "
            f"P/L {position.profit_loss:.2f}"
        )

    print("\nNo order was created.")
    print("No order endpoint was called.")


if __name__ == "__main__":
    main()