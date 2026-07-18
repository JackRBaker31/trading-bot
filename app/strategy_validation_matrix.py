from dataclasses import dataclass

from app.historical_data import HistoricalPrice
from app.risk import RiskLimits
from app.strategy_comparison import (
    StrategyComparisonRow,
)
from app.strategy_comparison_runner import (
    StrategyComparisonRunner,
)
from app.strategy_definition import (
    StrategyDefinition,
)
from app.walk_forward_windows import (
    create_walk_forward_windows,
)


@dataclass(frozen=True)
class StrategyValidationResult:
    window_number: int
    strategy_result: StrategyComparisonRow


class StrategyValidationMatrix:
    def __init__(
        self,
        *,
        starting_cash: float,
        risk_limits: RiskLimits,
    ) -> None:
        self.runner = StrategyComparisonRunner(
            starting_cash=starting_cash,
            risk_limits=risk_limits,
        )

    def run(
        self,
        *,
        historical_prices: list[HistoricalPrice],
        strategy_definitions: list[
            StrategyDefinition
        ],
        training_size: int,
        validation_size: int,
        step_size: int,
    ) -> list[StrategyValidationResult]:
        if not strategy_definitions:
            raise ValueError(
                "At least one strategy definition is required."
            )

        windows = create_walk_forward_windows(
            historical_prices=historical_prices,
            training_size=training_size,
            validation_size=validation_size,
            step_size=step_size,
        )

        results: list[
            StrategyValidationResult
        ] = []

        for window_number, window in enumerate(
            windows,
            start=1,
        ):
            validation_rows, _ = self.runner.run(
                historical_prices=(
                    window.validation_prices
                ),
                strategy_definitions=(
                    strategy_definitions
                ),
            )

            for row in validation_rows:
                results.append(
                    StrategyValidationResult(
                        window_number=window_number,
                        strategy_result=row,
                    )
                )

        return results