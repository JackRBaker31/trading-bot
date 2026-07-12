from datetime import date

from app.backtest import BacktestEngine
from app.buy_the_dip import BuyTheDipStrategy
from app.execution import ExecutionService
from app.historical_data import HistoricalPrice
from app.logging_config import setup_logging
from app.portfolio import Portfolio
from app.risk import RiskEngine, RiskLimits
from app.trade_log import TradeLog


def main() -> None:
    setup_logging(
        log_file="data/backtest_application.log"
    )

    historical_prices = [
        HistoricalPrice(
            trading_date=date(2026, 1, 2),
            prices={
                "AAPL": 150.00,
                "MSFT": 320.00,
            },
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 3),
            prices={
                "AAPL": 146.00,
                "MSFT": 318.00,
            },
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 4),
            prices={
                "AAPL": 142.00,
                "MSFT": 310.00,
            },
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 5),
            prices={
                "AAPL": 145.00,
                "MSFT": 315.00,
            },
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 6),
            prices={
                "AAPL": 149.00,
                "MSFT": 322.00,
            },
        ),
    ]

    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    risk_limits = RiskLimits(
        max_order_value=2_000.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        max_trades_per_session=10,
        approved_symbols={"AAPL", "MSFT"},
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

    strategy = BuyTheDipStrategy(
        drop_threshold_percent=2.0,
        quantity=5,
        cooldown_cycles=2,
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