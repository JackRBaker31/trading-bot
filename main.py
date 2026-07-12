import logging
from datetime import datetime

from app.buy_the_dip import BuyTheDipStrategy
from app.config import load_config
from app.execution import ExecutionService
from app.logging_config import setup_logging
from app.portfolio_store import PortfolioStore
from app.risk import RiskEngine, RiskLimits
from app.simulated_market_data import SimulatedMarketDataProvider
from app.trade_log import TradeLog
from app.trading_loop import TradingLoop


logger = logging.getLogger(__name__)


def main() -> None:
    setup_logging()

    logger.info("application_starting")

    config = load_config()

    print("Trading system starting...")
    print(f"Current time: {datetime.now()}")
    print(f"Mode: {config.mode}")
    print("Real-money trading: DISABLED")

    logger.info(
        "safe_mode_confirmed mode=%s real_money_trading=false",
        config.mode,
    )

    simulated_starting_prices = {
        "AAPL": 150.00,
        "MSFT": 320.00,
    }

    missing_symbols = [
        symbol
        for symbol in config.symbols
        if symbol not in simulated_starting_prices
    ]

    if missing_symbols:
        logger.error(
            "missing_simulated_prices symbols=%s",
            ",".join(missing_symbols),
        )

        raise ValueError(
            "No simulated starting price exists for: "
            + ", ".join(missing_symbols)
        )

    market_data = SimulatedMarketDataProvider(
        prices={
            symbol: simulated_starting_prices[symbol]
            for symbol in config.symbols
        }
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
        quantity=config.strategy.quantity,
        cooldown_cycles=(
            config.strategy.cooldown_cycles
        ),
    )

    def simulate_price_changes(
        cycle_number: int,
    ) -> None:
        if cycle_number == 2:
            if "AAPL" in config.symbols:
                market_data.set_price("AAPL", 146.00)

            if "MSFT" in config.symbols:
                market_data.set_price("MSFT", 318.00)

        elif cycle_number == 3:
            if "AAPL" in config.symbols:
                market_data.set_price("AAPL", 142.00)

            if "MSFT" in config.symbols:
                market_data.set_price("MSFT", 310.00)

        elif cycle_number == 4:
            if "AAPL" in config.symbols:
                market_data.set_price("AAPL", 138.00)

            if "MSFT" in config.symbols:
                market_data.set_price("MSFT", 308.00)

        elif cycle_number == 5:
            if "AAPL" in config.symbols:
                market_data.set_price("AAPL", 134.00)

            if "MSFT" in config.symbols:
                market_data.set_price("MSFT", 305.00)

    trading_loop = TradingLoop(
        symbols=config.symbols,
        market_data=market_data,
        strategy=strategy,
        execution_service=execution_service,
        interval_seconds=(
            config.trading_loop.interval_seconds
        ),
    )

    trading_loop.run(
        cycles=config.trading_loop.cycles,
        before_cycle=simulate_price_changes,
    )

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