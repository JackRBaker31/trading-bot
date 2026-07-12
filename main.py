from datetime import datetime

from app.buy_the_dip import BuyTheDipStrategy
from app.execution import ExecutionService
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

    strategy = BuyTheDipStrategy()

    print("\nReading initial prices...")

    initial_prices = market_data.get_prices(
        ["AAPL", "MSFT"]
    )

    initial_orders = strategy.generate_orders(initial_prices)

    print(
        f"Orders generated from initial prices: "
        f"{len(initial_orders)}"
    )

    print("\nSimulating price changes...")

    market_data.set_price("AAPL", 146.00)
    market_data.set_price("MSFT", 315.00)

    updated_prices = market_data.get_prices(
        ["AAPL", "MSFT"]
    )

    orders = strategy.generate_orders(updated_prices)

    print(f"Orders generated after price changes: {len(orders)}")

    for order in orders:
        print(
            f"\nStrategy proposed: "
            f"{order.side.value} "
            f"{order.quantity} {order.symbol} "
            f"at £{order.price:.2f}"
        )

        executed = execution_service.submit_order(
            order=order,
            current_prices=updated_prices,
        )

        print(
            f"Result: "
            f"{'EXECUTED' if executed else 'REJECTED'}"
        )

    portfolio.display(updated_prices)
    trade_log.display()


if __name__ == "__main__":
    main()