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


class StrategyOptimizer:
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

    def optimize(
        self,
        *,
        historical_prices: list[HistoricalPrice],
        drop_thresholds: list[float],
        sma_periods: list[int | None],
        rsi_settings: list[
            tuple[int | None, float | None]
        ],
        cooldown_cycles: list[int],
        target_allocation_percent: float,
    ) -> list[StrategyComparisonRow]:
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

        rows, _ = self.runner.run(
            historical_prices=historical_prices,
            strategy_definitions=definitions,
        )

        return rows