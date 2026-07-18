from dataclasses import dataclass

from app.historical_data import HistoricalPrice


@dataclass(frozen=True)
class WalkForwardWindow:
    training_prices: list[HistoricalPrice]
    validation_prices: list[HistoricalPrice]


def create_walk_forward_windows(
    *,
    historical_prices: list[HistoricalPrice],
    training_size: int,
    validation_size: int,
    step_size: int,
) -> list[WalkForwardWindow]:
    if not historical_prices:
        raise ValueError(
            "Historical prices are required."
        )

    if training_size <= 0:
        raise ValueError(
            "Training size must be positive."
        )

    if validation_size <= 0:
        raise ValueError(
            "Validation size must be positive."
        )

    if step_size <= 0:
        raise ValueError(
            "Step size must be positive."
        )

    sorted_prices = sorted(
        historical_prices,
        key=lambda price: price.trading_date,
    )

    required_size = (
        training_size
        + validation_size
    )

    if len(sorted_prices) < required_size:
        raise ValueError(
            "Not enough historical prices for "
            "one walk-forward window."
        )

    windows: list[
        WalkForwardWindow
    ] = []

    start_index = 0

    while (
        start_index
        + required_size
        <= len(sorted_prices)
    ):
        training_end = (
            start_index
            + training_size
        )

        validation_end = (
            training_end
            + validation_size
        )

        windows.append(
            WalkForwardWindow(
                training_prices=sorted_prices[
                    start_index:training_end
                ],
                validation_prices=sorted_prices[
                    training_end:validation_end
                ],
            )
        )

        start_index += step_size

    return windows