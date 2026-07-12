from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class HistoricalPrice:
    trading_date: date
    prices: dict[str, float]

    def __post_init__(self) -> None:
        if not self.prices:
            raise ValueError(
                "Historical prices cannot be empty."
            )

        cleaned_prices: dict[str, float] = {}

        for symbol, price in self.prices.items():
            cleaned_symbol = symbol.upper().strip()

            if not cleaned_symbol:
                raise ValueError(
                    "Historical price symbols cannot be empty."
                )

            if price <= 0:
                raise ValueError(
                    f"Historical price for "
                    f"{cleaned_symbol} must be positive."
                )

            cleaned_prices[cleaned_symbol] = float(price)

        object.__setattr__(
            self,
            "prices",
            cleaned_prices,
        )