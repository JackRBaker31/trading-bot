from dataclasses import dataclass, field


@dataclass(frozen=True)
class EquityPoint:
    label: str
    portfolio_value: float


@dataclass(frozen=True)
class BacktestResult:
    starting_cash: float
    ending_value: float
    total_return_percent: float
    maximum_drawdown_percent: float
    benchmark_return_percent: float
    excess_return_percent: float
    average_exposure_percent: float
    executed_trades: int
    rejected_orders: int
    profit_factor: float
    win_rate_percent: float
    maximum_consecutive_wins: int
    maximum_consecutive_losses: int
    average_winning_trade: float
    average_losing_trade: float
    largest_winning_trade: float
    largest_losing_trade: float
    expectancy: float
    final_cash: float
    final_positions: dict[str, int]
    equity_curve: list[EquityPoint] = field(
        default_factory=list
    )

    @property
    def calmar_ratio(
        self,
    ) -> float:
        if self.maximum_drawdown_percent == 0:
            if self.total_return_percent > 0:
                return float("inf")

            return 0.0

        return (
            self.total_return_percent
            / self.maximum_drawdown_percent
        )

    def display(self) -> None:
        print("\n================================")
        print("BACKTEST RESULTS")
        print("================================")
        print(
            f"Starting capital: "
            f"£{self.starting_cash:.2f}"
        )
        print(
            f"Ending portfolio value: "
            f"£{self.ending_value:.2f}"
        )
        print(
            f"Calmar ratio: "
            f"{self.calmar_ratio:.2f}"
        )
        print(
            f"Total return: "
            f"{self.total_return_percent:.2f}%"
        )
        print(
            f"Maximum drawdown: "
            f"{self.maximum_drawdown_percent:.2f}%"
        )
        print(
            f"Benchmark return: "
            f"{self.benchmark_return_percent:.2f}%"
        )
        print(
            f"Excess return: "
            f"{self.excess_return_percent:.2f}%"
        )
        print(
            f"Average exposure: "
            f"{self.average_exposure_percent:.2f}%"
        )
        print(
            f"Win rate: "
            f"{self.win_rate_percent:.2f}%"
        )
        print(
            f"Average winning trade: "
            f"£{self.average_winning_trade:.2f}"
        )
        print(
            f"Average losing trade: "
            f"£{self.average_losing_trade:.2f}"
        )
        print(
            f"Maximum consecutive wins: "
            f"{self.maximum_consecutive_wins}"
        )
        print(
            f"Maximum consecutive losses: "
            f"{self.maximum_consecutive_losses}"
        )
        print(
            f"Largest winning trade: "
            f"£{self.largest_winning_trade:.2f}"
        )
        print(
            f"Largest losing trade: "
            f"£{self.largest_losing_trade:.2f}"
        )
        print(
            f"Expectancy per trade: "
            f"£{self.expectancy:.2f}"
        )
        print(
            f"Executed trades: "
            f"{self.executed_trades}"
        )
        print(
            f"Rejected orders: "
            f"{self.rejected_orders}"
        )
        print(
            f"Profit factor: "
            f"{self.profit_factor:.2f}"
        )
        print(
            f"Final cash: "
            f"£{self.final_cash:.2f}"
        )
        print(
            f"Final positions: "
            f"{self.final_positions}"
        )
        print("================================")