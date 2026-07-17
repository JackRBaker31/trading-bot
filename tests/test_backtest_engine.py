from datetime import date

import pytest

from app.backtest_engine import (
    BacktestEngine,
)
from app.backtest_models import (
    HistoricalPriceBar,
)
from app.buy_the_dip import (
    BuyTheDipStrategy,
)


def test_backtest_executes_buy_signal(
        tmp_path,
    ) -> None:
    engine = BacktestEngine(
        strategy=BuyTheDipStrategy(
            drop_threshold_percent=2.0,
            target_allocation_percent=10.0,
        ),
        starting_cash=10_000.00,
        trade_log_path=(
            tmp_path
            / "backtest_trade_log.jsonl"
        ),
    )

    bars = [
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 7, 16),
            open_price=150.00,
            high_price=151.00,
            low_price=149.00,
            close_price=150.00,
            volume=1_000,
        ),
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 7, 17),
            open_price=147.00,
            high_price=148.00,
            low_price=145.00,
            close_price=146.00,
            volume=1_000,
        ),
    ]

    result = engine.run(
        bars=bars,
    )

    assert result.trade_count == 1
    assert result.ending_value == pytest.approx(
        10_000.00
    )


def test_backtest_marks_open_position_to_market(
    tmp_path,
) -> None:
    engine = BacktestEngine(
        strategy=BuyTheDipStrategy(
            drop_threshold_percent=2.0,
            target_allocation_percent=10.0,
        ),
        starting_cash=10_000.00,
        trade_log_path=(
            tmp_path
            / "backtest_trade_log.jsonl"
        ),
    )

    bars = [
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 7, 16),
            open_price=150.00,
            high_price=151.00,
            low_price=149.00,
            close_price=150.00,
            volume=1_000,
        ),
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 7, 17),
            open_price=147.00,
            high_price=148.00,
            low_price=145.00,
            close_price=146.00,
            volume=1_000,
        ),
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 7, 18),
            open_price=152.00,
            high_price=156.00,
            low_price=151.00,
            close_price=155.00,
            volume=1_000,
        ),
    ]

    result = engine.run(
        bars=bars,
    )

    assert result.ending_value > 10_000.00


def test_backtest_rejects_empty_bars() -> None:
    engine = BacktestEngine(
        strategy=BuyTheDipStrategy(
            drop_threshold_percent=2.0,
            target_allocation_percent=10.0,
        ),
        starting_cash=10_000.00,
    )

    with pytest.raises(
        ValueError,
        match="bars",
    ):
        engine.run(
            bars=[],
        )

from app.orders import (
    Order,
    OrderSide,
)


class BuyThenSellStrategy:
    def __init__(self) -> None:
        self._calls = 0

    def generate_orders(
        self,
        *,
        prices,
        portfolio,
    ):
        self._calls += 1

        if self._calls == 1:
            return [
                Order(
                    symbol="AAPL",
                    side=OrderSide.BUY,
                    quantity=2,
                    price=100.00,
                )
            ]

        if self._calls == 2:
            return [
                Order(
                    symbol="AAPL",
                    side=OrderSide.SELL,
                    quantity=2,
                    price=120.00,
                )
            ]

        return []


def test_backtest_counts_winning_trade(
    tmp_path,
) -> None:
    engine = BacktestEngine(
        strategy=BuyThenSellStrategy(),
        starting_cash=10_000.00,
        trade_log_path=(
            tmp_path
            / "backtest_trade_log.jsonl"
        ),
    )

    bars = [
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 7, 16),
            open_price=100.00,
            high_price=101.00,
            low_price=99.00,
            close_price=100.00,
            volume=1_000,
        ),
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 7, 17),
            open_price=120.00,
            high_price=121.00,
            low_price=119.00,
            close_price=120.00,
            volume=1_000,
        ),
    ]

    result = engine.run(
        bars=bars,
    )

    assert result.trade_count == 2
    assert result.winning_trade_count == 1
    assert result.losing_trade_count == 0
    assert result.win_rate_percent == 100.0