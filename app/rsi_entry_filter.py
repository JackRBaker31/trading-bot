from app.technical_indicators import (
    relative_strength_index,
)


class RsiEntryFilter:
    def __init__(
        self,
        period: int,
        buy_threshold: float,
    ) -> None:
        if period <= 0:
            raise ValueError(
                "RSI period must be positive."
            )

        if not 0 <= buy_threshold <= 100:
            raise ValueError(
                "RSI buy threshold must be between 0 and 100."
            )

        self.period = period
        self.buy_threshold = buy_threshold

    def allows_entry(
        self,
        *,
        symbol: str,
        current_price: float,
        price_history: list[float],
    ) -> bool:
        del symbol

        values = [
            *price_history,
            current_price,
        ]

        if len(values) < self.period + 1:
            return False

        rsi = relative_strength_index(
            values=values,
            period=self.period,
        )

        return rsi <= self.buy_threshold