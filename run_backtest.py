from app.backtest import BacktestEngine
from app.buy_the_dip import BuyTheDipStrategy
from app.csv_historical_data import (
    load_historical_prices_from_csv,
)
from app.execution import ExecutionService
from app.logging_config import setup_logging
from app.portfolio import Portfolio
from app.risk import RiskEngine, RiskLimits
from app.trade_log import TradeLog
from app.config import load_config
from app.rsi_entry_filter import RsiEntryFilter


def main() -> None:
    config = load_config()
    setup_logging(
        log_file="data/backtest_application.log"
    )

    historical_prices = (
        load_historical_prices_from_csv(
            file_path="data/sample_prices.csv"
        )
    )

    symbols = set(
        historical_prices[0].prices.keys()
    )

    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    risk_limits = RiskLimits(
        max_order_value=2_000.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        max_trades_per_session=100,
        approved_symbols=symbols,
    )

    risk_engine = RiskEngine(
        limits=risk_limits
    )

    trade_log = TradeLog(
        file_path="data/backtest_trade_log.jsonl"
    )

    execution_service = ExecutionService(
        portfolio=portfolio,
        risk_engine=risk_engine,
        trade_log=trade_log,
    )

    entry_filters = []

    if (
        config.strategy.rsi_period is not None
        and config.strategy.rsi_buy_threshold
        is not None
    ):
        entry_filters.append(
            RsiEntryFilter(
                period=config.strategy.rsi_period,
                buy_threshold=(
                    config.strategy
                    .rsi_buy_threshold
                ),
            )
        )

    strategy = BuyTheDipStrategy(
        drop_threshold_percent=(
            config.strategy
            .drop_threshold_percent
        ),
        target_allocation_percent=(
            config.strategy
            .target_allocation_percent
        ),
        cooldown_cycles=(
            config.strategy.cooldown_cycles
        ),
        sma_period=(
            config.strategy.sma_period
        ),
        entry_filters=entry_filters,
    )

    backtest_engine = BacktestEngine(
        portfolio=portfolio,
        strategy=strategy,
        execution_service=execution_service,
    )

    result = backtest_engine.run(
        historical_prices=historical_prices
    )

    result.display()

    print("\nEquity curve:")

    for point in result.equity_curve:
        print(
            f"{point.label}: "
            f"£{point.portfolio_value:.2f}"
        )


if __name__ == "__main__":
    main()