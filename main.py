from datetime import datetime

from app.orders import Order, OrderSide
from app.portfolio import Portfolio
from app.risk import RiskEngine, RiskLimits


def execute_order(
    order: Order,
    portfolio: Portfolio,
    risk_engine: RiskEngine,
    current_prices: dict[str, float],
) -> None:
    decision = risk_engine.evaluate(
        order=order,
        portfolio=portfolio,
        current_prices=current_prices,
    )

    print(f"\nProposed order: {order.side.value}")
    print(f"Symbol: {order.symbol}")
    print(f"Quantity: {order.quantity}")
    print(f"Price: £{order.price:.2f}")
    print(f"Order value: £{order.value:.2f}")
    print(f"Risk decision: {decision.reason}")

    if not decision.approved:
        print("Order rejected.")
        return

    if order.side == OrderSide.BUY:
        portfolio.buy(
            symbol=order.symbol,
            quantity=order.quantity,
            price=order.price,
        )
    else:
        portfolio.sell(
            symbol=order.symbol,
            quantity=order.quantity,
            price=order.price,
        )

    print("Order executed in simulation.")


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

    first_order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=10,
        price=current_prices["AAPL"],
    )

    execute_order(
        order=first_order,
        portfolio=portfolio,
        risk_engine=risk_engine,
        current_prices=current_prices,
    )

    rejected_order = Order(
        symbol="TSLA",
        side=OrderSide.BUY,
        quantity=2,
        price=current_prices["TSLA"],
    )

    execute_order(
        order=rejected_order,
        portfolio=portfolio,
        risk_engine=risk_engine,
        current_prices=current_prices,
    )

    portfolio.display(current_prices)


if __name__ == "__main__":
    main()