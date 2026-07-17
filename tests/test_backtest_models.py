from datetime import (
    date,
)

import pytest

from app.backtest_models import (
    BacktestResult,
    HistoricalPriceBar,
)


def test_creates_historical_price_bar() -> None:
    bar = HistoricalPriceBar(
        symbol=" aapl ",
        trading_date=date(
            2026,
            7,
            17,
        ),
        open_price=150.00,
        high_price=155.00,
        low_price=148.00,
        close_price=153.00,
        volume=1_000_000,
    )

    assert bar.symbol == "AAPL"
    assert bar.open_price == 150.00
    assert bar.high_price == 155.00
    assert bar.low_price == 148.00
    assert bar.close_price == 153.00
    assert bar.volume == 1_000_000


@pytest.mark.parametrize(
    (
        "open_price",
        "high_price",
        "low_price",
        "close_price",
    ),
    [
        (0.0, 155.0, 148.0, 153.0),
        (150.0, 0.0, 148.0, 153.0),
        (150.0, 155.0, 0.0, 153.0),
        (150.0, 155.0, 148.0, 0.0),
    ],
)
def test_rejects_non_positive_prices(
    open_price: float,
    high_price: float,
    low_price: float,
    close_price: float,
) -> None:
    with pytest.raises(
        ValueError,
    ):
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(
                2026,
                7,
                17,
            ),
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=1_000,
        )


def test_rejects_invalid_price_range() -> None:
    with pytest.raises(
        ValueError,
        match="High price",
    ):
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(
                2026,
                7,
                17,
            ),
            open_price=150.00,
            high_price=149.00,
            low_price=148.00,
            close_price=153.00,
            volume=1_000,
        )


def test_rejects_negative_volume() -> None:
    with pytest.raises(
        ValueError,
        match="Volume",
    ):
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(
                2026,
                7,
                17,
            ),
            open_price=150.00,
            high_price=155.00,
            low_price=148.00,
            close_price=153.00,
            volume=-1,
        )


def test_backtest_result_calculates_return_percent() -> None:
    result = BacktestResult(
        starting_cash=10_000.00,
        ending_value=11_500.00,
        trade_count=8,
        winning_trade_count=5,
        losing_trade_count=3,
        maximum_drawdown_percent=7.5,
    )

    assert result.return_percent == pytest.approx(
        15.0
    )
    assert result.win_rate_percent == pytest.approx(
        62.5
    )


def test_backtest_result_handles_zero_trades() -> None:
    result = BacktestResult(
        starting_cash=10_000.00,
        ending_value=10_000.00,
        trade_count=0,
        winning_trade_count=0,
        losing_trade_count=0,
        maximum_drawdown_percent=0.0,
    )

    assert result.return_percent == 0.0
    assert result.win_rate_percent == 0.0