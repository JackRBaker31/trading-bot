from datetime import datetime

from app.execution import ExecutionService
from app.orders import Order, OrderSide
from app.portfolio import Portfolio
from app.risk import RiskEngine, RiskLimits
from app.simulated_market_data import SimulatedMarketDataProvider
from app.trade_log import TradeLog


def main() -> None:
    print("Trading system starting...")
    print(f"Current time: {datetime.now()}")
    print("Mode: SAFE DEVELOPMENT MODE")
    print("Real-money trading: DISABLED")

    market_data = SimulatedMarketDataProvider(
        prices={
            "AAPL": 150.00,
            "MSFT": 320.00,
            "TSLA": 250.00,
        }
    )

    portfolio = Portfolio(starting_cash=10_000.00)

    risk_limits = RiskLimits(
        max_order_value=2_000.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        approved_symbols={"AAPL", "MSFT"},
    )

    risk_engine = RiskEngine(limits=risk_limits)
    trade_log = TradeLog()

    execution_service = ExecutionService(
        portfolio=portfolio,
        risk_engine=risk_engine,
        trade_log=trade_log,
    )

    current_prices = market_data.get_prices(
        ["AAPL", "MSFT", "TSLA"]
    )

    buy_order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=10,
        price=current_prices["AAPL"],
    )

    buy_executed = execution_service.submit_order(
        order=buy_order,
        current_prices=current_prices,
    )

    print(
        f"\nAAPL buy result: "
        f"{'EXECUTED' if buy_executed else 'REJECTED'}"
    )

    print("\nSimulating an AAPL price increase...")
    market_data.set_price("AAPL", 155.00)

    updated_prices = market_data.get_prices(
        ["AAPL", "MSFT", "TSLA"]
    )

    portfolio.display(updated_prices)
    trade_log.display()


if __name__ == "__main__":
    main()