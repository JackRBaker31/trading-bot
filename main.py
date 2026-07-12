from datetime import datetime

from app.execution import ExecutionService
from app.orders import Order, OrderSide
from app.portfolio import Portfolio
from app.risk import RiskEngine, RiskLimits
from app.trade_log import TradeLog


def display_order_result(order: Order, executed: bool) -> None:
    print("\nProposed order")
    print(f"Side: {order.side.value}")
    print(f"Symbol: {order.symbol}")
    print(f"Quantity: {order.quantity}")
    print(f"Price: £{order.price:.2f}")
    print(f"Value: £{order.value:.2f}")
    print(f"Result: {'EXECUTED' if executed else 'REJECTED'}")


def main() -> None:
    print("Trading system starting...")
    print(f"Current time: {datetime.now()}")
    print("Mode: SAFE DEVELOPMENT MODE")
    print("Real-money trading: DISABLED")

    current_prices = {
        "AAPL": 150.00,
        "MSFT": 320.00,
        "TSLA": 250.00,
    }

    portfolio = Portfolio(starting_cash=10_000.00)

    limits = RiskLimits(
        max_order_value=2_000.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        approved_symbols={"AAPL", "MSFT"},
    )

    risk_engine = RiskEngine(limits=limits)
    trade_log = TradeLog()

    execution_service = ExecutionService(
        portfolio=portfolio,
        risk_engine=risk_engine,
        trade_log=trade_log,
    )

    orders = [
        Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10,
            price=current_prices["AAPL"],
        ),
        Order(
            symbol="TSLA",
            side=OrderSide.BUY,
            quantity=2,
            price=current_prices["TSLA"],
        ),
        Order(
            symbol="AAPL",
            side=OrderSide.SELL,
            quantity=4,
            price=155.00,
        ),
    ]

    for order in orders:
        executed = execution_service.submit_order(
            order=order,
            current_prices=current_prices,
        )

        display_order_result(order, executed)

    current_prices["AAPL"] = 155.00

    portfolio.display(current_prices)
    trade_log.display()


if __name__ == "__main__":
    main()