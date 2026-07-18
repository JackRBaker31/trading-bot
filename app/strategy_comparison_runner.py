from app.backtest import BacktestEngine
from app.backtest_result import BacktestResult
from app.execution import ExecutionService
from app.historical_data import HistoricalPrice
from app.portfolio import Portfolio
from app.risk import RiskEngine, RiskLimits
from app.strategy import Strategy
from app.strategy_comparison import (
    StrategyComparisonRow,
    compare_strategy_results,
)
from app.trade_log import TradeLog
from app.strategy_definition import (
    StrategyDefinition,
)

class StrategyComparisonRunner:
    def __init__(
        self,
        *,
        starting_cash: float,
        risk_limits: RiskLimits,
    ) -> None:
        if starting_cash <= 0:
            raise ValueError(
                "Starting cash must be positive."
            )

        self.starting_cash = starting_cash
        self.risk_limits = risk_limits

    def run(
        self,
        *,
        historical_prices: list[HistoricalPrice],
        strategy_definitions: list[
            StrategyDefinition
        ],
    ) -> tuple[
        list[StrategyComparisonRow],
        dict[str, BacktestResult],
    ]:
        if not strategy_definitions:
            raise ValueError(
                "At least one strategy definition is required."
    )
        results: dict[str, BacktestResult] = {}

        for definition in strategy_definitions:
            portfolio = Portfolio(
                starting_cash=self.starting_cash
            )
            trade_log = TradeLog()
            execution_service = ExecutionService(
                portfolio=portfolio,
                risk_engine=RiskEngine(
                    self.risk_limits
                ),
                trade_log=trade_log,
            )
            engine = BacktestEngine(
                portfolio=portfolio,
                strategy=definition.factory(),
                execution_service=execution_service,
            )

            results[definition.name] = engine.run(
                historical_prices=historical_prices
            )

        return (
            compare_strategy_results(results),
            results,
        )