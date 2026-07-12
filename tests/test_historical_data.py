from datetime import date

import pytest

from app.historical_data import HistoricalPrice


def test_historical_price_cleans_symbols() -> None:
    price_point = HistoricalPrice(
        trading_date=date(2026, 1, 2),
        prices={
            " aapl ": 150.00,
        },
    )

    assert price_point.prices == {
        "AAPL": 150.00,
    }


def test_historical_price_rejects_empty_prices() -> None:
    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        HistoricalPrice(
            trading_date=date(2026, 1, 2),
            prices={},
        )


def test_historical_price_rejects_invalid_price() -> None:
    with pytest.raises(
        ValueError,
        match="must be positive",
    ):
        HistoricalPrice(
            trading_date=date(2026, 1, 2),
            prices={
                "AAPL": 0,
            },
        )