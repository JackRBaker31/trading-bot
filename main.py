from datetime import datetime

from app.buy_the_dip import BuyTheDipStrategy
from app.execution import ExecutionService
from app.portfolio import Portfolio
from app.risk import RiskEngine, RiskLimits
from app.simulated_market_data import SimulatedMarketDataProvider
from app.trade_log import TradeLog
from app.trading_loop import TradingLoop


def main() -> None:
    print("Trading system starting...")
    print(f"Current time: {datetime.now()}")
    print("Mode: SAFE DEVELOPMENT MODE")
    print("Real-money trading: DISABLED")

    market_data = SimulatedMarketDataProvider(
        prices={
            "AAPL": 150.00,
            "MSFT": 320.00,
        }
    )

    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    risk_limits = RiskLimits(
        max_order_value=2_000.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        approved_symbols={"AAPL", "MSFT"},
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

    strategy = BuyTheDipStrategy()

    def simulate_price_changes(
        cycle_number: int,
    ) -> None:
        if cycle_number == 2:
            market_data.set_price("AAPL", 146.00)
            market_data.set_price("MSFT", 318.00)

        elif cycle_number == 3:
            market_data.set_price("AAPL", 145.00)
            market_data.set_price("MSFT", 310.00)

        elif cycle_number == 4:
            market_data.set_price("AAPL", 149.00)
            market_data.set_price("MSFT", 312.00)

    trading_loop = TradingLoop(
        symbols=["AAPL", "MSFT"],
        market_data=market_data,
        strategy=strategy,
        execution_service=execution_service,
        interval_seconds=1.0,
    )

    trading_loop.run(
        cycles=4,
        before_cycle=simulate_price_changes,
    )

    final_prices = market_data.get_prices(
        ["AAPL", "MSFT"]
    )

    portfolio.display(final_prices)
    trade_log.display()


if __name__ == "__main__":
    main()