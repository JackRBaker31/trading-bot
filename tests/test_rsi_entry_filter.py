import pytest

from app.rsi_entry_filter import RsiEntryFilter


def test_allows_entry_when_rsi_is_below_threshold() -> None:
    entry_filter = RsiEntryFilter(
        period=3,
        buy_threshold=30.0,
    )

    result = entry_filter.allows_entry(
        symbol="AAPL",
        current_price=90.0,
        price_history=[
            100.0,
            100.0,
            100.0,
        ],
    )

    assert result is True


def test_blocks_entry_when_rsi_is_above_threshold() -> None:
    entry_filter = RsiEntryFilter(
        period=3,
        buy_threshold=30.0,
    )

    result = entry_filter.allows_entry(
        symbol="AAPL",
        current_price=102.0,
        price_history=[
            100.0,
            99.0,
            101.0,
        ],
    )

    assert result is False


def test_blocks_entry_until_enough_prices_exist() -> None:
    entry_filter = RsiEntryFilter(
        period=3,
        buy_threshold=30.0,
    )

    result = entry_filter.allows_entry(
        symbol="AAPL",
        current_price=90.0,
        price_history=[
            100.0,
            100.0,
        ],
    )

    assert result is False


def test_includes_current_price_in_rsi_calculation() -> None:
    entry_filter = RsiEntryFilter(
        period=3,
        buy_threshold=30.0,
    )
    price_history = [
        100.0,
        100.0,
        100.0,
    ]

    result = entry_filter.allows_entry(
        symbol="AAPL",
        current_price=90.0,
        price_history=price_history,
    )

    assert result is True
    assert price_history == [
        100.0,
        100.0,
        100.0,
    ]


@pytest.mark.parametrize(
    "period",
    [
        0,
        -1,
    ],
)
def test_rejects_non_positive_period(
    period: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="RSI period must be positive",
    ):
        RsiEntryFilter(
            period=period,
            buy_threshold=30.0,
        )


@pytest.mark.parametrize(
    "buy_threshold",
    [
        -0.1,
        100.1,
    ],
)
def test_rejects_threshold_outside_rsi_range(
    buy_threshold: float,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "RSI buy threshold must be between "
            "0 and 100"
        ),
    ):
        RsiEntryFilter(
            period=3,
            buy_threshold=buy_threshold,
        )