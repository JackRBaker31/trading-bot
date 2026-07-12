import logging

from app.backtest_result import (
    BacktestResult,
    EquityPoint,
)
from app.execution import ExecutionService
from app.historical_data import HistoricalPrice
from app.portfolio import Portfolio
from app.strategy import Strategy


logger = logging.getLogger(__name__)


class BacktestEngine:
    def __init__(
        self,
        portfolio: Portfolio,
        strategy: Strategy,
        execution_service: ExecutionService,
    ) -> None:
        self.portfolio = portfolio
        self.strategy = strategy
        self.execution_service = execution_service

    def run(
        self,
        historical_prices: list[HistoricalPrice],
    ) -> BacktestResult:
        if not historical_prices:
            raise ValueError(
                "At least one historical price point is required."
            )

        logger.info(
            "backtest_started price_points=%s",
            len(historical_prices),
        )

        starting_cash = self.portfolio.starting_cash
        equity_curve: list[EquityPoint] = []

        for price_point in historical_prices:
            current_prices = price_point.prices

            logger.info(
                "backtest_day date=%s prices=%s",
                price_point.trading_date,
                current_prices,
            )

            orders = self.strategy.generate_orders(
                current_prices
            )

            for order in orders:
                self.execution_service.submit_order(
                    order=order,
                    current_prices=current_prices,
                )

            portfolio_value = self.portfolio.portfolio_value(
                current_prices
            )

            equity_curve.append(
                EquityPoint(
                    label=price_point.trading_date.isoformat(),
                    portfolio_value=portfolio_value,
                )
            )

        final_prices = historical_prices[-1].prices

        ending_value = self.portfolio.portfolio_value(
            final_prices
        )

        total_return_percent = (
            (ending_value - starting_cash)
            / starting_cash
        ) * 100

        executed_trades = sum(
            1
            for entry in self.execution_service.trade_log.entries
            if entry.executed
        )

        rejected_orders = sum(
            1
            for entry in self.execution_service.trade_log.entries
            if not entry.executed
        )

        result = BacktestResult(
            starting_cash=starting_cash,
            ending_value=ending_value,
            total_return_percent=total_return_percent,
            executed_trades=executed_trades,
            rejected_orders=rejected_orders,
            final_cash=self.portfolio.cash,
            final_positions=dict(
                self.portfolio.positions
            ),
            equity_curve=equity_curve,
        )

        logger.info(
            "backtest_finished ending_value=%.2f "
            "return_percent=%.2f "
            "executed_trades=%s rejected_orders=%s",
            result.ending_value,
            result.total_return_percent,
            result.executed_trades,
            result.rejected_orders,
        )

        return result