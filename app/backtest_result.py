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
    executed_trades: int
    rejected_orders: int
    final_cash: float
    final_positions: dict[str, int]
    equity_curve: list[EquityPoint] = field(
        default_factory=list
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
            f"Total return: "
            f"{self.total_return_percent:.2f}%"
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
            f"Final cash: "
            f"£{self.final_cash:.2f}"
        )
        print(
            f"Final positions: "
            f"{self.final_positions}"
        )
        print("================================")