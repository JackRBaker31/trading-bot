import pytest

from app.portfolio import Portfolio


def test_portfolio_starts_with_correct_cash() -> None:
    portfolio = Portfolio(starting_cash=10_000.00)

    assert portfolio.cash == 10_000.00
    assert portfolio.positions == {}


def test_buy_reduces_cash_and_adds_position() -> None:
    portfolio = Portfolio(starting_cash=10_000.00)

    portfolio.buy(symbol="AAPL", quantity=10, price=150.00)

    assert portfolio.cash == 8_500.00
    assert portfolio.positions["AAPL"] == 10


def test_sell_increases_cash_and_reduces_position() -> None:
    portfolio = Portfolio(starting_cash=10_000.00)

    portfolio.buy(symbol="AAPL", quantity=10, price=150.00)
    portfolio.sell(symbol="AAPL", quantity=4, price=155.00)

    assert portfolio.cash == 9_120.00
    assert portfolio.positions["AAPL"] == 6


def test_selling_all_shares_removes_position() -> None:
    portfolio = Portfolio(starting_cash=10_000.00)

    portfolio.buy(symbol="AAPL", quantity=10, price=150.00)
    portfolio.sell(symbol="AAPL", quantity=10, price=155.00)

    assert "AAPL" not in portfolio.positions


def test_cannot_buy_more_than_available_cash() -> None:
    portfolio = Portfolio(starting_cash=1_000.00)

    with pytest.raises(ValueError, match="Insufficient cash"):
        portfolio.buy(symbol="AAPL", quantity=10, price=150.00)


def test_cannot_sell_more_shares_than_owned() -> None:
    portfolio = Portfolio(starting_cash=10_000.00)

    portfolio.buy(symbol="AAPL", quantity=5, price=150.00)

    with pytest.raises(ValueError, match="Insufficient shares"):
        portfolio.sell(symbol="AAPL", quantity=10, price=155.00)


def test_profit_and_loss_is_calculated_correctly() -> None:
    portfolio = Portfolio(starting_cash=10_000.00)

    portfolio.buy(symbol="AAPL", quantity=10, price=150.00)

    current_prices = {"AAPL": 155.00}

    assert portfolio.profit_and_loss(current_prices) == 50.00