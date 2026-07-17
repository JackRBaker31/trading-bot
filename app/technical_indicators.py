from app.backtest_models import HistoricalPriceBar

def simple_moving_average(
    values: list[float],
    period: int,
) -> float:
    if period <= 0:
        raise ValueError("Period must be positive")

    if len(values) < period:
        raise ValueError("Not enough values for period")

    recent_values = values[-period:]

    return sum(recent_values) / period

def exponential_moving_average(
    values: list[float],
    period: int,
) -> float:
    ema = simple_moving_average(
        values=values[:period],
        period=period,
    )
    multiplier = 2 / (period + 1)

    for value in values[period:]:
        ema = (
            (value - ema) * multiplier
            + ema
        )

    return ema

def relative_strength_index(
    values: list[float],
    period: int,
) -> float:
    if period <= 0:
        raise ValueError("Period must be positive")

    if len(values) < period + 1:
        raise ValueError("Not enough values for period")

    changes = [
        current - previous
        for previous, current in zip(
            values,
            values[1:],
            strict=False,
        )
    ]
    recent_changes = changes[-period:]

    gains = [
        change
        for change in recent_changes
        if change > 0
    ]
    losses = [
        -change
        for change in recent_changes
        if change < 0
    ]

    average_gain = sum(gains) / period
    average_loss = sum(losses) / period

    if average_gain == 0 and average_loss == 0:
        return 50.0

    if average_loss == 0:
        return 100.0

    relative_strength = average_gain / average_loss

    return 100 - (
        100 / (1 + relative_strength)
    )

def true_range(
    high: float,
    low: float,
    previous_close: float,
) -> float:
    return max(
        high - low,
        abs(high - previous_close),
        abs(low - previous_close),
    )

def average_true_range(
    bars: list[HistoricalPriceBar],
    period: int,
) -> float:
    if period <= 0:
        raise ValueError("Period must be positive")

    if len(bars) < period:
        raise ValueError("Not enough bars for period")

    start_index = len(bars) - period
    true_ranges: list[float] = []

    for index in range(start_index, len(bars)):
        bar = bars[index]

        if index == 0:
            bar_true_range = (
                bar.high_price
                - bar.low_price
            )
        else:
            bar_true_range = true_range(
                high=bar.high_price,
                low=bar.low_price,
                previous_close=bars[index - 1].close_price,
            )

        true_ranges.append(
            bar_true_range
        )

    return sum(true_ranges) / period