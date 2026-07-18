from datetime import date, timedelta

import pytest

from app.historical_data import HistoricalPrice
from app.walk_forward_windows import (
    create_walk_forward_windows,
)


def create_prices(
    count: int,
) -> list[HistoricalPrice]:
    start_date = date(
        2026,
        1,
        1,
    )

    return [
        HistoricalPrice(
            trading_date=(
                start_date
                + timedelta(days=index)
            ),
            prices={
                "AAPL": 100.0 + index,
            },
        )
        for index in range(count)
    ]


def test_creates_rolling_walk_forward_windows() -> None:
    windows = create_walk_forward_windows(
        historical_prices=create_prices(10),
        training_size=4,
        validation_size=2,
        step_size=2,
    )

    assert len(windows) == 3

    assert [
        price.trading_date
        for price in windows[0].training_prices
    ] == [
        date(2026, 1, 1),
        date(2026, 1, 2),
        date(2026, 1, 3),
        date(2026, 1, 4),
    ]

    assert [
        price.trading_date
        for price in windows[0].validation_prices
    ] == [
        date(2026, 1, 5),
        date(2026, 1, 6),
    ]

    assert windows[1].training_prices[0].trading_date == (
        date(2026, 1, 3)
    )

    assert windows[2].validation_prices[-1].trading_date == (
        date(2026, 1, 10)
    )


def test_sorts_prices_before_creating_windows() -> None:
    historical_prices = list(
        reversed(
            create_prices(6)
        )
    )

    windows = create_walk_forward_windows(
        historical_prices=historical_prices,
        training_size=4,
        validation_size=2,
        step_size=1,
    )

    assert (
        windows[0]
        .training_prices[0]
        .trading_date
        == date(2026, 1, 1)
    )


@pytest.mark.parametrize(
    (
        "training_size",
        "validation_size",
        "step_size",
        "message",
    ),
    [
        (
            0,
            2,
            1,
            "Training size",
        ),
        (
            4,
            0,
            1,
            "Validation size",
        ),
        (
            4,
            2,
            0,
            "Step size",
        ),
    ],
)
def test_rejects_non_positive_window_sizes(
    training_size: int,
    validation_size: int,
    step_size: int,
    message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=message,
    ):
        create_walk_forward_windows(
            historical_prices=create_prices(10),
            training_size=training_size,
            validation_size=validation_size,
            step_size=step_size,
        )


def test_rejects_insufficient_history() -> None:
    with pytest.raises(
        ValueError,
        match="Not enough historical prices",
    ):
        create_walk_forward_windows(
            historical_prices=create_prices(5),
            training_size=4,
            validation_size=2,
            step_size=1,
        )