from datetime import date
import pytest
from app.backtest_models import HistoricalPriceBar

from app.technical_indicators import (
    exponential_moving_average,
    relative_strength_index,
    simple_moving_average,
    true_range,
    average_true_range,
)


def test_calculates_simple_moving_average() -> None:
    result = simple_moving_average(
        values=[
            10.0,
            12.0,
            14.0,
            16.0,
        ],
        period=3,
    )

    assert result == pytest.approx(
        14.0
    )

def test_rejects_non_positive_simple_moving_average_period() -> None:
    with pytest.raises(
        ValueError,
        match="Period must be positive",
    ):
        simple_moving_average(
            values=[
                10.0,
                12.0,
                14.0,
            ],
            period=0,
        )

def test_rejects_insufficient_values_for_simple_moving_average() -> None:
    with pytest.raises(
        ValueError,
        match="Not enough values for period",
    ):
        simple_moving_average(
            values=[
                10.0,
                12.0,
            ],
            period=3,
        )

def test_calculates_exponential_moving_average() -> None:
    result = exponential_moving_average(
        values=[
            10.0,
            11.0,
            12.0,
            15.0,
            14.0,
        ],
        period=3,
    )

    assert result == pytest.approx(
        13.5
    )

def test_rejects_non_positive_exponential_moving_average_period() -> None:
    with pytest.raises(
        ValueError,
        match="Period must be positive",
    ):
        exponential_moving_average(
            values=[
                10.0,
                12.0,
                14.0,
            ],
            period=0,
        )


def test_rejects_insufficient_values_for_exponential_moving_average() -> None:
    with pytest.raises(
        ValueError,
        match="Not enough values for period",
    ):
        exponential_moving_average(
            values=[
                10.0,
                12.0,
            ],
            period=3,
        )

def test_calculates_relative_strength_index() -> None:
    result = relative_strength_index(
        values=[
            10.0,
            11.0,
            12.0,
            11.0,
        ],
        period=3,
    )

    assert result == pytest.approx(
        66.6666666667
    )


def test_relative_strength_index_returns_one_hundred_for_only_gains() -> None:
    result = relative_strength_index(
        values=[
            10.0,
            11.0,
            12.0,
            13.0,
        ],
        period=3,
    )

    assert result == pytest.approx(
        100.0
    )

def test_rejects_non_positive_relative_strength_index_period() -> None:
    with pytest.raises(
        ValueError,
        match="Period must be positive",
    ):
        relative_strength_index(
            values=[
                10.0,
                11.0,
            ],
            period=0,
        )


def test_rejects_insufficient_values_for_relative_strength_index() -> None:
    with pytest.raises(
        ValueError,
        match="Not enough values for period",
    ):
        relative_strength_index(
            values=[
                10.0,
                11.0,
                12.0,
            ],
            period=3,
        )


def test_relative_strength_index_returns_zero_for_only_losses() -> None:
    result = relative_strength_index(
        values=[
            13.0,
            12.0,
            11.0,
            10.0,
        ],
        period=3,
    )

    assert result == pytest.approx(
        0.0
    )


def test_relative_strength_index_returns_fifty_for_flat_prices() -> None:
    result = relative_strength_index(
        values=[
            10.0,
            10.0,
            10.0,
            10.0,
        ],
        period=3,
    )

    assert result == pytest.approx(
        50.0
    )

def test_calculates_true_range_from_high_and_low() -> None:
    result = true_range(
        high=15.0,
        low=10.0,
        previous_close=12.0,
    )

    assert result == pytest.approx(
        5.0
    )


def test_calculates_true_range_from_gap_up() -> None:
    result = true_range(
        high=15.0,
        low=13.0,
        previous_close=10.0,
    )

    assert result == pytest.approx(
        5.0
    )


def test_calculates_true_range_from_gap_down() -> None:
    result = true_range(
        high=10.0,
        low=8.0,
        previous_close=13.0,
    )

    assert result == pytest.approx(
        5.0
    )

def test_calculates_average_true_range() -> None:
    bars = [
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 7, 14),
            open_price=9.0,
            high_price=12.0,
            low_price=8.0,
            close_price=10.0,
            volume=1_000,
        ),
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 7, 15),
            open_price=11.0,
            high_price=15.0,
            low_price=11.0,
            close_price=14.0,
            volume=1_000,
        ),
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 7, 16),
            open_price=13.0,
            high_price=14.0,
            low_price=9.0,
            close_price=10.0,
            volume=1_000,
        ),
    ]

    result = average_true_range(
        bars=bars,
        period=3,
    )

    assert result == pytest.approx(
        14.0 / 3.0
    )

def test_rejects_non_positive_average_true_range_period() -> None:
    with pytest.raises(
        ValueError,
        match="Period must be positive",
    ):
        average_true_range(
            bars=[],
            period=0,
        )


def test_rejects_insufficient_bars_for_average_true_range() -> None:
    bars = [
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 7, 16),
            open_price=10.0,
            high_price=12.0,
            low_price=9.0,
            close_price=11.0,
            volume=1_000,
        ),
    ]

    with pytest.raises(
        ValueError,
        match="Not enough bars for period",
    ):
        average_true_range(
            bars=bars,
            period=2,
        )


def test_average_true_range_uses_previous_close_before_selected_window() -> None:
    bars = [
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 7, 14),
            open_price=10.0,
            high_price=11.0,
            low_price=9.0,
            close_price=10.0,
            volume=1_000,
        ),
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 7, 15),
            open_price=15.0,
            high_price=16.0,
            low_price=14.0,
            close_price=15.0,
            volume=1_000,
        ),
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 7, 16),
            open_price=15.0,
            high_price=17.0,
            low_price=14.0,
            close_price=16.0,
            volume=1_000,
        ),
    ]

    result = average_true_range(
        bars=bars,
        period=2,
    )

    assert result == pytest.approx(
        4.5
    )