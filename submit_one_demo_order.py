import argparse
import os
from pathlib import Path
from typing import Protocol

from dotenv import load_dotenv

from app.config import AppConfig, load_config
from app.logging_config import setup_logging
from app.market_data_factory import (
    create_market_data_provider,
)
from app.market_session import MarketSession
from app.order_journal import OrderJournal
from app.orders import Order, OrderSide
from app.paper_execution_factory import (
    create_paper_execution_adapter,
)
from app.portfolio_store import PortfolioStore
from app.risk import RiskEngine, RiskLimits
from app.symbol_mapping_service import (
    SymbolMappingService,
)
from app.trade_log import TradeLog
from app.trading212_client import Trading212Client
from app.paper_order_workflow import (
    PaperOrderWorkflowResult,
)


def parse_args(
    argv: list[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--confirm-demo-order",
        action="store_true",
        dest="confirm_demo_order",
        help=(
            "Explicitly confirm submission "
            "of one demo order."
        ),
    )

    args = parser.parse_args(argv)

    if not args.confirm_demo_order:
        parser.error(
            "--confirm-demo-order is required."
        )

    return args


def validate_config(
    config: AppConfig,
) -> None:
    if config.mode != "PAPER":
        raise RuntimeError(
            "One-shot demo order requires "
            "PAPER mode."
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
            "One-shot demo order requires "
            "the DEMO broker environment."
        )

    if config.market_data_provider != "TWELVE_DATA":
        raise RuntimeError(
            "One-shot demo order requires "
            "TWELVE_DATA market data."
        )

    if not (
        config.paper_trading
        .order_execution_permission_confirmed
    ):
        raise RuntimeError(
            "Order-execution permission has "
            "not been confirmed."
        )


def build_demo_order(
    symbol: str,
    price: float,
) -> Order:
    return Order(
        symbol=symbol,
        side=OrderSide.BUY,
        quantity=1,
        price=price,
    )


class OrderExecutionAdapter(Protocol):
    def submit_order_with_result(
        self,
        order: Order,
        current_prices: dict[str, float],
    ) -> PaperOrderWorkflowResult:
        """Submit one order through the safe pipeline."""


def execute_demo_order(
    adapter: OrderExecutionAdapter,
    order: Order,
) -> PaperOrderWorkflowResult:
    return adapter.submit_order_with_result(
        order=order,
        current_prices={
            order.symbol: order.price,
        },
    )


def main() -> None:
    parse_args()

    setup_logging()
    load_dotenv()

    config = load_config()
    validate_config(config)

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
            "Trading 212 DEMO credentials "
            "were not found."
        )

    if not config.symbols:
        raise RuntimeError(
            "No configured symbol is available."
        )

    symbol = config.symbols[0]

    broker = Trading212Client(
        api_key=api_key,
        api_secret=api_secret,
        environment="DEMO",
    )

    active_orders = broker.get_active_orders()

    if active_orders:
        raise RuntimeError(
            "One-shot execution blocked because "
            "active broker orders already exist."
        )

    symbol_mapping = (
        SymbolMappingService().resolve(
            broker=broker,
            configured_symbols=[symbol],
        )
    )

    market_data = create_market_data_provider(
        provider_name=(
            config.market_data_provider
        ),
        symbols=[symbol],
    )

    prices = market_data.get_prices(
        [symbol]
    )

    price = prices.get(symbol)

    if price is None or price <= 0:
        raise RuntimeError(
            f"No valid current price was "
            f"available for {symbol}."
        )

    portfolio_store = PortfolioStore()
    portfolio = portfolio_store.load_or_create(
        starting_cash=config.starting_cash
    )

    risk_engine = RiskEngine(
        limits=RiskLimits(
            max_order_value=(
                config.risk.max_order_value
            ),
            max_position_value=(
                config.risk.max_position_value
            ),
            max_portfolio_exposure=(
                config.risk.max_portfolio_exposure
            ),
            max_trades_per_session=1,
            approved_symbols={symbol},
        )
    )

    trade_log = TradeLog(
        file_path=(
            "data/one_shot_demo_trade_log.jsonl"
        )
    )

    order_journal = OrderJournal(
    path=Path(
        "order_journal.jsonl"
    )
)

    market_session = MarketSession(
        timezone_name=(
            config.market_session.timezone
        ),
        opening_time=(
            config.market_session.opening_time
        ),
        closing_time=(
            config.market_session.closing_time
        ),
        trading_weekdays=set(
            config.market_session
            .trading_weekdays
        ),
    )

    adapter = create_paper_execution_adapter(
        api_key=api_key,
        api_secret=api_secret,
        symbol_mapping=symbol_mapping,
        portfolio=portfolio,
        risk_engine=risk_engine,
        trade_log=trade_log,
        order_journal=order_journal,
        paper_trading_enabled=True,
        broker_environment="DEMO",
        order_execution_permission_confirmed=True,
        market_session=market_session,
        enforce_market_hours=(
            config.market_session
            .enforce_market_hours
        ),
        max_poll_attempts=5,
        poll_interval_seconds=1.0,
    )

    order = build_demo_order(
        symbol=symbol,
        price=price,
    )

    print()
    print("ABOUT TO SUBMIT ONE DEMO ORDER")
    print("Environment: DEMO")
    print(f"Symbol: {order.symbol}")
    print(
        "Broker ticker: "
        f"{symbol_mapping[order.symbol]}"
    )
    print(f"Side: {order.side.value}")
    print(f"Quantity: {order.quantity}")
    print(f"Reference price: {order.price:.2f}")
    print(f"Estimated value: {order.value:.2f}")
    print()

    result = execute_demo_order(
        adapter=adapter,
        order=order,
    )

    if not result.submitted:
        raise RuntimeError(
            "The DEMO order was not submitted. "
            f"Reason: {result.reason}"
        )

    if result.portfolio_updated:
        portfolio_store.save(
            portfolio
        )

        print()
        print(
            "One Trading 212 DEMO order completed "
            "and was verified."
        )
        print(
            "The local portfolio was updated."
        )
        print(
            "No further orders will be submitted."
        )
        return

    verification_result = (
        result.verification_result
    )

    print()
    print(
        "The DEMO order was accepted by "
        "Trading 212."
    )

    if verification_result is not None:
        broker_order = (
            verification_result.broker_order
        )

        print(
            f"Broker order ID: "
            f"{broker_order.order_id}"
        )
        print(
            f"Broker status: "
            f"{broker_order.status}"
        )
        print(
            "Verification status: "
            f"{verification_result.status.value}"
        )

    print(
        "The order remains active or requires "
        "follow-up."
    )
    print(
        "The local portfolio was not updated."
    )
    print(
        "Do not submit another order. Recovery "
        "will inspect this order later."
    )
    print("No further orders will be submitted.")


if __name__ == "__main__":
    main()