import os

from dotenv import load_dotenv

from app.config import load_config
from app.logging_config import setup_logging
from app.trading212_client import Trading212Client
from app.instrument_resolver import (
    InstrumentResolver,
)


def main() -> None:
    setup_logging()
    load_dotenv()

    config = load_config()

    if config.mode != "PAPER":
        raise RuntimeError(
            "Readiness check requires PAPER mode."
        )

    if not config.paper_trading.enabled:
        raise RuntimeError(
            "Paper trading is disabled."
        )

    if (
        config.paper_trading.broker_environment
        != "DEMO"
    ):
        raise RuntimeError(
            "Readiness check requires the "
            "Trading 212 DEMO environment."
        )

    api_key = os.getenv(
        "TRADING212_API_KEY",
        "",
    ).strip()

    api_secret = os.getenv(
        "TRADING212_API_SECRET",
        "",
    ).strip()

    if not api_key or not api_secret:
        raise RuntimeError(
            "Trading 212 credentials were "
            "not found."
        )

    broker = Trading212Client(
        api_key=api_key,
        api_secret=api_secret,
        environment="DEMO",
    )

    account = broker.get_account_summary()
    positions = broker.get_positions()
    active_orders = broker.get_active_orders()
    instruments = broker.get_instruments()

    symbol_mapping = InstrumentResolver(
        instruments=instruments
    ).resolve_symbols(
        config.symbols
    )

    print()
    print(
        "Trading 212 DEMO connection successful."
    )
    print("Environment: DEMO")
    print(f"Account currency: {account.currency}")
    print(
        "Available to trade: "
        f"{account.available_to_trade:.2f}"
    )
    print(f"Open positions: {len(positions)}")
    print(f"Active orders: {len(active_orders)}")
    print(
        f"Execution permission confirmed: "
        f"{config.paper_trading.order_execution_permission_confirmed}"
    )
    print("No orders were submitted.")

    if active_orders:
        print()
        print(
            "READINESS BLOCKED: "
            "active broker orders require review."
        )

        for order in active_orders:
            print(
                f"- Order {order.order_id}: "
                f"{order.side} {order.quantity} "
                f"{order.ticker} ({order.status})"
            )

        raise RuntimeError(
            "Demo readiness failed because active "
            "broker orders exist."
        )

    print(
        f"Available instruments: "
        f"{len(instruments)}"
    )
    print("Resolved symbols:")

    for symbol, broker_ticker in (
        symbol_mapping.items()
    ):
        print(
            f"- {symbol} -> {broker_ticker}"
        )

    print()
    print(
        "READ-ONLY BROKER PREFLIGHT PASSED."
    )


if __name__ == "__main__":
    main()