from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class HistoricalPriceBar:
    symbol: str
    trading_date: date
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int

    def __post_init__(
        self,
    ) -> None:
        normalised_symbol = (
            self.symbol.upper().strip()
        )

        if not normalised_symbol:
            raise ValueError(
                "Symbol is required."
            )

        object.__setattr__(
            self,
            "symbol",
            normalised_symbol,
        )

        for price in (
            self.open_price,
            self.high_price,
            self.low_price,
            self.close_price,
        ):
            if price <= 0:
                raise ValueError(
                    "Prices must be positive."
                )

        if self.high_price < max(
            self.open_price,
            self.low_price,
            self.close_price,
        ):
            raise ValueError(
                "High price cannot be below "
                "another price."
            )

        if self.low_price > min(
            self.open_price,
            self.high_price,
            self.close_price,
        ):
            raise ValueError(
                "Low price cannot be above "
                "another price."
            )

        if self.volume < 0:
            raise ValueError(
                "Volume cannot be negative."
            )


@dataclass(frozen=True)
class BacktestResult:
    starting_cash: float
    ending_value: float
    trade_count: int
    winning_trade_count: int
    losing_trade_count: int
    maximum_drawdown_percent: float

    def __post_init__(
        self,
    ) -> None:
        if self.starting_cash <= 0:
            raise ValueError(
                "Starting cash must be positive."
            )

        if self.ending_value < 0:
            raise ValueError(
                "Ending value cannot be negative."
            )

        if self.trade_count < 0:
            raise ValueError(
                "Trade count cannot be negative."
            )

        if self.winning_trade_count < 0:
            raise ValueError(
                "Winning trade count cannot "
                "be negative."
            )

        if self.losing_trade_count < 0:
            raise ValueError(
                "Losing trade count cannot "
                "be negative."
            )

        if (
            self.winning_trade_count
            + self.losing_trade_count
            > self.trade_count
        ):
            raise ValueError(
                "Winning and losing trades cannot "
                "exceed total trades."
            )

        if self.maximum_drawdown_percent < 0:
            raise ValueError(
                "Maximum drawdown cannot "
                "be negative."
            )

    @property
    def return_percent(
        self,
    ) -> float:
        return (
            (
                self.ending_value
                - self.starting_cash
            )
            / self.starting_cash
            * 100.0
        )

    @property
    def win_rate_percent(
        self,
    ) -> float:
        completed_trade_count = (
            self.winning_trade_count
            + self.losing_trade_count
        )

        if completed_trade_count == 0:
            return 0.0

        return (
            self.winning_trade_count
            / completed_trade_count
            * 100.0
        )