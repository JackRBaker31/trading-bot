from app.orders import Order, OrderSide
from app.portfolio import Portfolio
from app.risk import RiskEngine, RiskLimits


def create_risk_engine() -> RiskEngine:
    limits = RiskLimits(
        max_order_value=2_000.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        approved_symbols={"AAPL", "MSFT"},
    )

    return RiskEngine(limits=limits)


def test_approved_buy_order_passes() -> None:
    portfolio = Portfolio(starting_cash=10_000.00)
    risk_engine = create_risk_engine()

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=10,
        price=150.00,
    )

    decision = risk_engine.evaluate(
        order=order,
        portfolio=portfolio,
        current_prices={"AAPL": 150.00},
    )

    assert decision.approved is True


def test_unapproved_symbol_is_rejected() -> None:
    portfolio = Portfolio(starting_cash=10_000.00)
    risk_engine = create_risk_engine()

    order = Order(
        symbol="TSLA",
        side=OrderSide.BUY,
        quantity=1,
        price=250.00,
    )

    decision = risk_engine.evaluate(
        order=order,
        portfolio=portfolio,
        current_prices={"TSLA": 250.00},
    )

    assert decision.approved is False
    assert "approved-symbol list" in decision.reason


def test_large_order_is_rejected() -> None:
    portfolio = Portfolio(starting_cash=10_000.00)
    risk_engine = create_risk_engine()

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=20,
        price=150.00,
    )

    decision = risk_engine.evaluate(
        order=order,
        portfolio=portfolio,
        current_prices={"AAPL": 150.00},
    )

    assert decision.approved is False
    assert "order limit" in decision.reason


def test_position_limit_is_enforced() -> None:
    portfolio = Portfolio(starting_cash=10_000.00)
    portfolio.buy(symbol="AAPL", quantity=15, price=150.00)

    risk_engine = create_risk_engine()

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=10,
        price=150.00,
    )

    decision = risk_engine.evaluate(
        order=order,
        portfolio=portfolio,
        current_prices={"AAPL": 150.00},
    )

    assert decision.approved is False
    assert "position limit" in decision.reason


def test_cannot_sell_more_than_owned() -> None:
    portfolio = Portfolio(starting_cash=10_000.00)
    portfolio.buy(symbol="AAPL", quantity=5, price=150.00)

    risk_engine = create_risk_engine()

    order = Order(
        symbol="AAPL",
        side=OrderSide.SELL,
        quantity=10,
        price=155.00,
    )

    decision = risk_engine.evaluate(
        order=order,
        portfolio=portfolio,
        current_prices={"AAPL": 155.00},
    )

    assert decision.approved is False
    assert "only 5 are owned" in decision.reason


def test_valid_sell_order_passes() -> None:
    portfolio = Portfolio(starting_cash=10_000.00)
    portfolio.buy(symbol="AAPL", quantity=5, price=150.00)

    risk_engine = create_risk_engine()

    order = Order(
        symbol="AAPL",
        side=OrderSide.SELL,
        quantity=3,
        price=155.00,
    )

    decision = risk_engine.evaluate(
        order=order,
        portfolio=portfolio,
        current_prices={"AAPL": 155.00},
    )

    assert decision.approved is True