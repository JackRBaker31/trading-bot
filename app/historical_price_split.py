from app.historical_data import HistoricalPrice


def split_historical_prices(
    *,
    historical_prices: list[HistoricalPrice],
    training_fraction: float,
) -> tuple[
    list[HistoricalPrice],
    list[HistoricalPrice],
]:
    if not historical_prices:
        raise ValueError(
            "Historical prices are required."
        )

    if not 0 < training_fraction < 1:
        raise ValueError(
            "Training fraction must be between 0 and 1."
        )

    if len(historical_prices) < 2:
        raise ValueError(
            "At least two historical price points are required."
        )

    sorted_prices = sorted(
        historical_prices,
        key=lambda price: price.trading_date,
    )

    split_index = int(
        len(sorted_prices)
        * training_fraction
    )

    split_index = max(
        1,
        min(
            split_index,
            len(sorted_prices) - 1,
        ),
    )

    return (
        sorted_prices[:split_index],
        sorted_prices[split_index:],
    )