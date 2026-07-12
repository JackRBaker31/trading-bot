import os

from dotenv import load_dotenv

from app.logging_config import setup_logging
from app.portfolio_store import PortfolioStore
from app.reconciliation import BrokerReconciler
from app.trading212_client import Trading212Client


def main() -> None:
    setup_logging()
    load_dotenv()

    api_key = os.getenv(
        "TRADING212_DEMO_API_KEY",
        "",
    ).strip()

    api_secret = os.getenv(
        "TRADING212_DEMO_API_SECRET",
        "",
    ).strip()

    if not api_key:
        raise RuntimeError(
            "TRADING212_DEMO_API_KEY was not "
            "found in .env."
        )

    if not api_secret:
        raise RuntimeError(
            "TRADING212_DEMO_API_SECRET was not "
            "found in .env."
        )

    client = Trading212Client(
        api_key=api_key,
        api_secret=api_secret,
        environment="DEMO",
    )

    portfolio_store = PortfolioStore()

    portfolio = portfolio_store.load_or_create(
        starting_cash=5_000.00
    )

    account_summary = (
        client.get_account_summary()
    )

    broker_positions = client.get_positions()

    reconciler = BrokerReconciler(
        symbol_mapping={
            "AAPL": "AAPL_US_EQ",
            "MSFT": "MSFT_US_EQ",
        }
    )

    report = reconciler.reconcile(
        portfolio=portfolio,
        account_summary=account_summary,
        broker_positions=broker_positions,
    )

    report.display()

    if not report.safe_to_trade:
        print(
            "\nTrading would be blocked until "
            "the mismatch is resolved."
        )


if __name__ == "__main__":
    main()