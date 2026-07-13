from pathlib import Path

import pytest

from app.portfolio import Portfolio
from app.portfolio_store import PortfolioStore


def test_store_saves_and_loads_portfolio(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "portfolio.json"

    store = PortfolioStore(
        file_path=str(file_path)
    )

    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    portfolio.buy(
        symbol="AAPL",
        quantity=5,
        price=150.00,
    )

    store.save(portfolio)

    loaded_portfolio = store.load()

    assert loaded_portfolio.starting_cash == 10_000.00
    assert loaded_portfolio.cash == 9_250.00
    assert loaded_portfolio.positions == {
        "AAPL": 5,
    }


def test_load_or_create_creates_new_portfolio(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "portfolio.json"

    store = PortfolioStore(
        file_path=str(file_path)
    )

    portfolio = store.load_or_create(
        starting_cash=10_000.00
    )

    assert portfolio.cash == 10_000.00
    assert portfolio.positions == {}
    assert file_path.exists()


def test_load_or_create_loads_existing_portfolio(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "portfolio.json"

    store = PortfolioStore(
        file_path=str(file_path)
    )

    original_portfolio = Portfolio(
        starting_cash=10_000.00
    )

    original_portfolio.buy(
        symbol="AAPL",
        quantity=2,
        price=150.00,
    )

    store.save(original_portfolio)

    loaded_portfolio = store.load_or_create(
        starting_cash=5_000.00
    )

    assert loaded_portfolio.starting_cash == 10_000.00
    assert loaded_portfolio.cash == 9_700.00
    assert loaded_portfolio.positions == {
        "AAPL": 2,
    }


def test_load_missing_portfolio_raises_error(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "missing.json"

    store = PortfolioStore(
        file_path=str(file_path)
    )

    with pytest.raises(FileNotFoundError):
        store.load()

def test_applied_broker_order_ids_are_persisted(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "portfolio.json"

    store = PortfolioStore(
        file_path=str(file_path)
    )

    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    portfolio.mark_broker_order_applied(
        broker_order_id=123456
    )
    portfolio.mark_broker_order_applied(
        broker_order_id=654321
    )

    store.save(portfolio)

    loaded_portfolio = store.load()

    assert (
        loaded_portfolio
        .applied_broker_order_ids
        == {
            123456,
            654321,
        }
    )

def test_legacy_portfolio_without_applied_ids_loads(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "portfolio.json"

    file_path.write_text(
        (
            "{\n"
            '  "starting_cash": 10000.0,\n'
            '  "cash": 9700.0,\n'
            '  "positions": {"AAPL": 2}\n'
            "}"
        ),
        encoding="utf-8",
    )

    store = PortfolioStore(
        file_path=str(file_path)
    )

    portfolio = store.load()

    assert portfolio.cash == 9_700.00
    assert portfolio.positions == {
        "AAPL": 2,
    }
    assert (
        portfolio.applied_broker_order_ids
        == set()
    )

def test_duplicate_broker_order_id_is_rejected() -> None:
    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    portfolio.mark_broker_order_applied(
        broker_order_id=123456
    )

    with pytest.raises(
        ValueError,
        match="already been applied",
    ):
        portfolio.mark_broker_order_applied(
            broker_order_id=123456
        )

    