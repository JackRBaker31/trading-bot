import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from app.buy_the_dip import BuyTheDipStrategy
from app.config import load_config
from app.execution import ExecutionService
from app.logging_config import setup_logging
from app.market_data_factory import create_market_data_provider
from app.portfolio_store import PortfolioStore
from app.risk import RiskEngine, RiskLimits
from app.simulated_market_data import SimulatedMarketDataProvider
from app.trade_log import TradeLog
from app.trading_loop import TradingLoop
from app.market_session import MarketSession
from app.demo_recovery_factory import (
    create_demo_recovery_startup_service,
)
from app.order_journal import OrderJournal


logger = logging.getLogger(__name__)


def main() -> None:
    setup_logging()
    load_dotenv()

    logger.info("application_starting")

    config = load_config()

    print("Trading system starting...")
    print(f"Current time: {datetime.now()}")
    print(f"Mode: {config.mode}")
    print(f"Market data: {config.market_data_provider}")
    print("Real-money trading: DISABLED")

    logger.info(
        "safe_mode_confirmed mode=%s "
        "market_data_provider=%s "
        "real_money_trading=false",
        config.mode,
        config.market_data_provider,
    )

    market_data = create_market_data_provider(
        provider_name=config.market_data_provider,
        symbols=config.symbols,
    )

    portfolio_store = PortfolioStore()

    portfolio = portfolio_store.load_or_create(
        starting_cash=config.starting_cash
    )

    risk_limits = RiskLimits(
        max_order_value=config.risk.max_order_value,
        max_position_value=config.risk.max_position_value,
        max_portfolio_exposure=(
            config.risk.max_portfolio_exposure
        ),
        max_trades_per_session=(
            config.risk.max_trades_per_session
        ),
        approved_symbols=set(config.symbols),
    )

    risk_engine = RiskEngine(
        limits=risk_limits
    )

    trade_log = TradeLog()

    execution_service = ExecutionService(
        portfolio=portfolio,
        risk_engine=risk_engine,
        trade_log=trade_log,
    )

    strategy = BuyTheDipStrategy(
        drop_threshold_percent=(
            config.strategy.drop_threshold_percent
        ),
        target_allocation_percent=(
            config.strategy.target_allocation_percent
        ),
        cooldown_cycles=(
            config.strategy.cooldown_cycles
        ),
    )

    def simulate_price_changes(
        cycle_number: int,
    ) -> None:
        if config.market_data_provider != "SIMULATED":
            return

        if not isinstance(
            market_data,
            SimulatedMarketDataProvider,
        ):
            return

        if cycle_number == 2:
            if "AAPL" in config.symbols:
                market_data.set_price(
                    "AAPL",
                    146.00,
                )

            if "MSFT" in config.symbols:
                market_data.set_price(
                    "MSFT",
                    318.00,
                )

        elif cycle_number == 3:
            if "AAPL" in config.symbols:
                market_data.set_price(
                    "AAPL",
                    142.00,
                )

            if "MSFT" in config.symbols:
                market_data.set_price(
                    "MSFT",
                    310.00,
                )

        elif cycle_number == 4:
            if "AAPL" in config.symbols:
                market_data.set_price(
                    "AAPL",
                    138.00,
                )

            if "MSFT" in config.symbols:
                market_data.set_price(
                    "MSFT",
                    308.00,
                )

        elif cycle_number == 5:
            if "AAPL" in config.symbols:
                market_data.set_price(
                    "AAPL",
                    134.00,
                )

            if "MSFT" in config.symbols:
                market_data.set_price(
                    "MSFT",
                    305.00,
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
        config.market_session.trading_weekdays
    ),
)

    trading_loop = TradingLoop(
        symbols=config.symbols,
        market_data=market_data,
        strategy=strategy,
        execution_service=execution_service,
        interval_seconds=(
            config.trading_loop.interval_seconds
        ),
        market_session=market_session,
        enforce_market_hours=(
            config.market_session
            .enforce_market_hours
        ),
    )

    def start_trading() -> None:
        trading_loop.run(
            cycles=config.trading_loop.cycles,
            before_cycle=simulate_price_changes,
        )


    if config.mode == "PAPER":
        if not config.paper_trading.enabled:
            raise ValueError(
                "PAPER mode requires paper trading "
                "to be enabled."
            )

        if (
            config.paper_trading.broker_environment
            != "DEMO"
        ):
            raise ValueError(
                "PAPER mode requires the Trading 212 "
                "DEMO environment."
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
            raise ValueError(
                "Trading 212 Demo credentials are "
                "required for startup recovery."
            )

        order_journal = OrderJournal(
            path=Path("order_journal.jsonl")
        )

        recovery_startup_service = (
            create_demo_recovery_startup_service(
                api_key=api_key,
                api_secret=api_secret,
                order_journal=order_journal,
                portfolio=portfolio,
                portfolio_store=portfolio_store,
            )
        )

        startup_result = (
            recovery_startup_service.start(
                start_trading=start_trading
            )
        )

        if not startup_result.trading_started:
            logger.error(
                "trading_refused_by_startup_recovery "
                "reason=%s incomplete_items=%s",
                startup_result.decision.reason,
                (
                    startup_result
                    .recovery_report
                    .incomplete_items
                ),
            )

            print(
                "Trading refused: "
                f"{startup_result.decision.reason}"
            )
            return
    else:
        start_trading()

    portfolio_store.save(portfolio)

    print("\nPortfolio saved.")

    final_prices = market_data.get_prices(
        config.symbols
    )

    portfolio.display(final_prices)
    trade_log.display()

    logger.info(
        "application_finished cash=%.2f positions=%s "
        "session_trade_count=%s",
        portfolio.cash,
        portfolio.positions,
        risk_engine.executed_trade_count,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception(
            "application_stopped_due_to_unhandled_error"
        )
        raise