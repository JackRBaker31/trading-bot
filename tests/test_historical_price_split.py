from datetime import date

import pytest

from app.historical_data import HistoricalPrice
from app.historical_price_split import (
    split_historical_prices,
)


def create_price(
    year: int,
    month: int,
    day: int,
) -> HistoricalPrice:
    return HistoricalPrice(
        trading_date=date(
            year,
            month,
            day,
        ),
        prices={
            "AAPL": 100.0,
        },
    )


def test_splits_prices_chronologically() -> None:
    historical_prices = [
        create_price(2026, 1, 4),
        create_price(2026, 1, 2),
        create_price(2026, 1, 3),
        create_price(2026, 1, 5),
    ]

    training, validation = (
        split_historical_prices(
            historical_prices=historical_prices,
            training_fraction=0.75,
        )
    )

    assert [
        price.trading_date
        for price in training
    ] == [
        date(2026, 1, 2),
        date(2026, 1, 3),
        date(2026, 1, 4),
    ]

    assert [
        price.trading_date
        for price in validation
    ] == [
        date(2026, 1, 5),
    ]


def test_keeps_at_least_one_price_in_each_part() -> None:
    historical_prices = [
        create_price(2026, 1, 2),
        create_price(2026, 1, 3),
    ]

    training, validation = (
        split_historical_prices(
            historical_prices=historical_prices,
            training_fraction=0.99,
        )
    )

    assert len(training) == 1
    assert len(validation) == 1


@pytest.mark.parametrize(
    "training_fraction",
    [
        0.0,
        1.0,
        -0.1,
        1.1,
    ],
)
def test_rejects_invalid_training_fraction(
    training_fraction: float,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Training fraction must be "
            "between 0 and 1"
        ),
    ):
        split_historical_prices(
            historical_prices=[
                create_price(2026, 1, 2),
                create_price(2026, 1, 3),
            ],
            training_fraction=training_fraction,
        )


def test_rejects_insufficient_history() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "At least two historical price points"
        ),
    ):
        split_historical_prices(
            historical_prices=[
                create_price(2026, 1, 2),
            ],
            training_fraction=0.8,
        )