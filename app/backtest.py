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
        exposure_percentages: list[float] = []

        for price_point in historical_prices:
            current_prices = price_point.prices

            logger.info(
                "backtest_day date=%s prices=%s",
                price_point.trading_date,
                current_prices,
            )

            orders = self.strategy.generate_orders(
            prices=current_prices,
            portfolio=self.portfolio,
        )

            for order in orders:
                self.execution_service.submit_order(
                    order=order,
                    current_prices=current_prices,
                )

            portfolio_value = self.portfolio.portfolio_value(
                current_prices
            )

            exposure_value = self._calculate_exposure_value(
                current_prices=current_prices
            )

            exposure_percent = (
                exposure_value / portfolio_value
            ) * 100

            exposure_percentages.append(
                exposure_percent
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

        maximum_drawdown_percent = (
            self._calculate_maximum_drawdown(
                equity_curve
            )
        )

        benchmark_return_percent = (
            self._calculate_equal_weight_benchmark_return(
                historical_prices
            )
        )

        excess_return_percent = (
            total_return_percent
            - benchmark_return_percent
        )

        average_exposure_percent = (
            sum(exposure_percentages)
            / len(exposure_percentages)
        )

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
            maximum_drawdown_percent=(
                maximum_drawdown_percent
            ),
            benchmark_return_percent=(
                benchmark_return_percent
            ),
            excess_return_percent=(
                excess_return_percent
            ),
            average_exposure_percent=(
                average_exposure_percent
            ),
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
            "max_drawdown_percent=%.2f "
            "benchmark_return_percent=%.2f "
            "excess_return_percent=%.2f "
            "average_exposure_percent=%.2f "
            "executed_trades=%s "
            "rejected_orders=%s",
            result.ending_value,
            result.total_return_percent,
            result.maximum_drawdown_percent,
            result.benchmark_return_percent,
            result.excess_return_percent,
            result.average_exposure_percent,
            result.executed_trades,
            result.rejected_orders,
        )

        return result

    def _calculate_exposure_value(
        self,
        current_prices: dict[str, float],
    ) -> float:
        exposure_value = 0.0

        for symbol, quantity in self.portfolio.positions.items():
            if symbol not in current_prices:
                raise ValueError(
                    f"No current price was supplied for {symbol}."
                )

            exposure_value += (
                quantity * current_prices[symbol]
            )

        return exposure_value

    @staticmethod
    def _calculate_maximum_drawdown(
        equity_curve: list[EquityPoint],
    ) -> float:
        peak_value = equity_curve[0].portfolio_value
        maximum_drawdown = 0.0

        for point in equity_curve:
            if point.portfolio_value > peak_value:
                peak_value = point.portfolio_value

            drawdown = (
                (peak_value - point.portfolio_value)
                / peak_value
            ) * 100

            maximum_drawdown = max(
                maximum_drawdown,
                drawdown,
            )

        return maximum_drawdown

    @staticmethod
    def _calculate_equal_weight_benchmark_return(
        historical_prices: list[HistoricalPrice],
    ) -> float:
        first_prices = historical_prices[0].prices
        last_prices = historical_prices[-1].prices

        if set(first_prices) != set(last_prices):
            raise ValueError(
                "Benchmark symbols are inconsistent."
            )

        symbol_returns: list[float] = []

        for symbol, starting_price in first_prices.items():
            ending_price = last_prices[symbol]

            symbol_return = (
                (ending_price - starting_price)
                / starting_price
            ) * 100

            symbol_returns.append(
                symbol_return
            )

        return sum(symbol_returns) / len(
            symbol_returns
        )