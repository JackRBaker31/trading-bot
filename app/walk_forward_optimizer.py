from app.historical_data import HistoricalPrice
from app.historical_price_split import (
    split_historical_prices,
)
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
from app.strategy_grid import (
    generate_buy_the_dip_definitions,
)
from app.strategy_optimizer import (
    StrategyOptimizer,
)


class WalkForwardOptimizer:
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
        training_fraction: float,
        drop_thresholds: list[float],
        sma_periods: list[int | None],
        rsi_settings: list[
            tuple[int | None, float | None]
        ],
        cooldown_cycles: list[int],
        target_allocation_percent: float,
    ) -> tuple[
        StrategyComparisonRow,
        StrategyComparisonRow,
    ]:
        training_prices, validation_prices = (
            split_historical_prices(
                historical_prices=historical_prices,
                training_fraction=training_fraction,
            )
        )

        training_rows = self.optimizer.optimize(
            historical_prices=training_prices,
            drop_thresholds=drop_thresholds,
            sma_periods=sma_periods,
            rsi_settings=rsi_settings,
            cooldown_cycles=cooldown_cycles,
            target_allocation_percent=(
                target_allocation_percent
            ),
        )

        winning_name = training_rows[0].name

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

        winning_definition = next(
            definition
            for definition in definitions
            if definition.name == winning_name
        )

        validation_rows, _ = self.runner.run(
            historical_prices=validation_prices,
            strategy_definitions=[
                StrategyDefinition(
                    name=winning_definition.name,
                    factory=winning_definition.factory,
                )
            ],
        )

        return (
            training_rows[0],
            validation_rows[0],
        )