from dataclasses import dataclass

from app.historical_data import HistoricalPrice
from app.risk import RiskLimits
from app.strategy_comparison import (
    StrategyComparisonRow,
)
from app.strategy_comparison_runner import (
    StrategyComparisonRunner,
)
from app.strategy_grid import (
    generate_buy_the_dip_definitions,
)
from app.strategy_optimizer import (
    StrategyOptimizer,
)
from app.walk_forward_windows import (
    create_walk_forward_windows,
)


@dataclass(frozen=True)
class RollingWalkForwardResult:
    window_number: int
    training_result: StrategyComparisonRow
    validation_result: StrategyComparisonRow


class RollingWalkForwardOptimizer:
    def __init__(
        self,
        *,
        starting_cash: float,
        risk_limits: RiskLimits,
    ) -> None:
        self.optimizer = StrategyOptimizer(
            starting_cash=starting_cash,
            risk_limits=risk_limits,
        )
        self.runner = StrategyComparisonRunner(
            starting_cash=starting_cash,
            risk_limits=risk_limits,
        )

    def run(
        self,
        *,
        historical_prices: list[HistoricalPrice],
        training_size: int,
        validation_size: int,
        step_size: int,
        drop_thresholds: list[float],
        sma_periods: list[int | None],
        rsi_settings: list[
            tuple[int | None, float | None]
        ],
        cooldown_cycles: list[int],
        target_allocation_percent: float,
    ) -> list[RollingWalkForwardResult]:
        windows = create_walk_forward_windows(
            historical_prices=historical_prices,
            training_size=training_size,
            validation_size=validation_size,
            step_size=step_size,
        )

        definitions = (
            generate_buy_the_dip_definitions(
                drop_thresholds=drop_thresholds,
                sma_periods=sma_periods,
                rsi_settings=rsi_settings,
                cooldown_cycles=cooldown_cycles,
                target_allocation_percent=(
                    target_allocation_percent
                ),
            )
        )

        results: list[
            RollingWalkForwardResult
        ] = []

        for window_number, window in enumerate(
            windows,
            start=1,
        ):
            training_rows = (
                self.optimizer.optimize(
                    historical_prices=(
                        window.training_prices
                    ),
                    drop_thresholds=(
                        drop_thresholds
                    ),
                    sma_periods=sma_periods,
                    rsi_settings=rsi_settings,
                    cooldown_cycles=(
                        cooldown_cycles
                    ),
                    target_allocation_percent=(
                        target_allocation_percent
                    ),
                )
            )

            winning_name = (
                training_rows[0].name
            )

            winning_definition = next(
                definition
                for definition in definitions
                if definition.name == winning_name
            )

            validation_rows, _ = (
                self.runner.run(
                    historical_prices=(
                        window.validation_prices
                    ),
                    strategy_definitions=[
                        winning_definition
                    ],
                )
            )

            results.append(
                RollingWalkForwardResult(
                    window_number=window_number,
                    training_result=(
                        training_rows[0]
                    ),
                    validation_result=(
                        validation_rows[0]
                    ),
                )
            )

        return results