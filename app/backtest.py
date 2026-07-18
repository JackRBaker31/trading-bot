import logging

from app.backtest_models import HistoricalPriceBar
from app.backtest_result import (
    BacktestResult,
    EquityPoint,
)
from app.completed_trade_tracker import (
    CompletedTradeTracker,
)
from app.execution import ExecutionService
from app.historical_data import HistoricalPrice
from app.orders import OrderSide
from app.portfolio import Portfolio
from app.position_exit_manager import (
    PositionExitManager,
)
from app.position_state import PositionState
from app.strategy import Strategy


logger = logging.getLogger(__name__)


class BacktestEngine:
    def __init__(
        self,
        portfolio: Portfolio,
        strategy: Strategy,
        execution_service: ExecutionService,
        position_exit_manager: (
            PositionExitManager | None
        ) = None,
    ) -> None:
        self.portfolio = portfolio
        self.strategy = strategy
        self.execution_service = (
            execution_service
        )
        self.position_exit_manager = (
            position_exit_manager
        )

    def run_bars(
        self,
        bars: list[HistoricalPriceBar],
    ) -> BacktestResult:
        if not bars:
            raise ValueError(
                "At least one historical price bar is required."
            )

        prices_by_date: dict[
            object,
            dict[str, float],
        ] = {}

        for bar in bars:
            daily_prices = (
                prices_by_date.setdefault(
                    bar.trading_date,
                    {},
                )
            )

            if bar.symbol in daily_prices:
                raise ValueError(
                    "Duplicate historical price bar for "
                    f"{bar.symbol} on "
                    f"{bar.trading_date.isoformat()}."
                )

            daily_prices[bar.symbol] = (
                bar.close_price
            )

        historical_prices = [
            HistoricalPrice(
                trading_date=trading_date,
                prices=prices_by_date[
                    trading_date
                ],
            )
            for trading_date in sorted(
                prices_by_date
            )
        ]

        return self.run(
            historical_prices=historical_prices
        )

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

        starting_cash = (
            self.portfolio.starting_cash
        )
        equity_curve: list[EquityPoint] = []
        exposure_percentages: list[
            float
        ] = []
        trade_tracker = (
            CompletedTradeTracker()
        )
        position_states: dict[
            str,
            PositionState,
        ] = {}

        for price_point in historical_prices:
            current_prices = (
                price_point.prices
            )

            logger.info(
                "backtest_day date=%s prices=%s",
                price_point.trading_date,
                current_prices,
            )

            orders = list(
                self.strategy.generate_orders(
                    prices=current_prices,
                    portfolio=self.portfolio,
                )
            )

            if (
                self.position_exit_manager
                is not None
                and position_states
            ):
                exit_orders = (
                    self.position_exit_manager
                    .generate_exit_orders(
                        positions=position_states,
                        current_prices=(
                            current_prices
                        ),
                    )
                )

                orders.extend(
                    exit_orders
                )

            for order in orders:
                executed = (
                    self.execution_service
                    .submit_order(
                        order=order,
                        current_prices=current_prices,
                    )
                )

                if not executed:
                    continue

                executed_price = (
                    self.execution_service
                    .trade_log.entries[-1]
                    .price
                )

                if order.side is OrderSide.BUY:
                    # Completed-trade accounting uses the real,
                    # cost-adjusted execution price.
                    trade_tracker.record_buy(
                        symbol=order.symbol,
                        quantity=order.quantity,
                        price=executed_price,
                    )

                    existing_state = (
                        position_states.get(
                            order.symbol
                        )
                    )

                    if existing_state is None:
                        # Exit-policy state uses the market price
                        # originally seen by the strategy. This keeps
                        # gross and net runs on the same decision path.
                        position_states[
                            order.symbol
                        ] = PositionState(
                            symbol=order.symbol,
                            quantity=order.quantity,
                            average_entry_price=(
                                order.price
                            ),
                        )
                    else:
                        existing_state.add(
                            quantity=order.quantity,
                            price=order.price,
                        )

                else:
                    # Completed-trade accounting uses the real,
                    # cost-adjusted execution price.
                    trade_tracker.record_sell(
                        symbol=order.symbol,
                        quantity=order.quantity,
                        price=executed_price,
                    )

                    existing_state = (
                        position_states.get(
                            order.symbol
                        )
                    )

                    if existing_state is not None:
                        if (
                            order.quantity
                            >= existing_state.quantity
                        ):
                            position_states.pop(
                                order.symbol,
                                None,
                            )
                        else:
                            existing_state.reduce(
                                quantity=order.quantity,
                            )

            portfolio_value = (
                self.portfolio
                .portfolio_value(
                    current_prices
                )
            )

            exposure_value = (
                self._calculate_exposure_value(
                    current_prices=(
                        current_prices
                    )
                )
            )

            exposure_percent = (
                exposure_value
                / portfolio_value
                * 100
            )

            exposure_percentages.append(
                exposure_percent
            )

            equity_curve.append(
                EquityPoint(
                    label=(
                        price_point
                        .trading_date
                        .isoformat()
                    ),
                    portfolio_value=(
                        portfolio_value
                    ),
                )
            )

        final_prices = (
            historical_prices[-1].prices
        )

        ending_value = (
            self.portfolio
            .portfolio_value(
                final_prices
            )
        )

        total_return_percent = (
            (
                ending_value
                - starting_cash
            )
            / starting_cash
            * 100
        )

        maximum_drawdown_percent = (
            self._calculate_maximum_drawdown(
                equity_curve
            )
        )

        benchmark_return_percent = (
            self
            ._calculate_equal_weight_benchmark_return(
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
            for entry in (
                self.execution_service
                .trade_log.entries
            )
            if entry.executed
        )

        rejected_orders = sum(
            1
            for entry in (
                self.execution_service
                .trade_log.entries
            )
            if not entry.executed
        )

        result = BacktestResult(
            starting_cash=starting_cash,
            ending_value=ending_value,
            total_return_percent=(
                total_return_percent
            ),

            average_winning_trade=(
                trade_tracker
                .average_winning_trade
            ),
            average_losing_trade=(
                trade_tracker
                .average_losing_trade
            ),
            largest_winning_trade=(
                trade_tracker
                .largest_winning_trade
            ),
            largest_losing_trade=(
                trade_tracker
                .largest_losing_trade
            ),
            expectancy=(
                trade_tracker.expectancy
            ),
            win_rate_percent=(
                trade_tracker
                .win_rate_percent
            ),
            profit_factor=(
                trade_tracker.profit_factor
            ),
            completed_trade_returns_percent=[
                trade.return_percent
                for trade in (
                    trade_tracker
                    .completed_trades
                )
            ],
            completed_trade_profits=[
                trade.realised_profit
                for trade in trade_tracker.completed_trades
            ],
            maximum_drawdown_percent=(
                maximum_drawdown_percent
            ),
            benchmark_return_percent=(
                benchmark_return_percent
            ),
            excess_return_percent=(
                excess_return_percent
            ),
            maximum_consecutive_wins=(
                trade_tracker
                .maximum_consecutive_wins
            ),
            maximum_consecutive_losses=(
                trade_tracker
                .maximum_consecutive_losses
            ),
            average_exposure_percent=(
                average_exposure_percent
            ),
            executed_trades=(
                executed_trades
            ),
            rejected_orders=(
                rejected_orders
            ),
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
        current_prices: dict[
            str,
            float,
        ],
    ) -> float:
        exposure_value = 0.0

        for (
            symbol,
            quantity,
        ) in self.portfolio.positions.items():
            if symbol not in current_prices:
                raise ValueError(
                    "No current price was supplied "
                    f"for {symbol}."
                )

            exposure_value += (
                quantity
                * current_prices[symbol]
            )

        return exposure_value

    @staticmethod
    def _calculate_maximum_drawdown(
        equity_curve: list[EquityPoint],
    ) -> float:
        peak_value = (
            equity_curve[0]
            .portfolio_value
        )
        maximum_drawdown = 0.0

        for point in equity_curve:
            if (
                point.portfolio_value
                > peak_value
            ):
                peak_value = (
                    point.portfolio_value
                )

            drawdown = (
                (
                    peak_value
                    - point.portfolio_value
                )
                / peak_value
                * 100
            )

            maximum_drawdown = max(
                maximum_drawdown,
                drawdown,
            )

        return maximum_drawdown

    @staticmethod
    def _calculate_equal_weight_benchmark_return(
        historical_prices: list[
            HistoricalPrice
        ],
    ) -> float:
        first_prices = (
            historical_prices[0].prices
        )
        last_prices = (
            historical_prices[-1].prices
        )

        if (
            set(first_prices)
            != set(last_prices)
        ):
            raise ValueError(
                "Benchmark symbols are inconsistent."
            )

        symbol_returns: list[
            float
        ] = []

        for (
            symbol,
            starting_price,
        ) in first_prices.items():
            ending_price = (
                last_prices[symbol]
            )

            symbol_return = (
                (
                    ending_price
                    - starting_price
                )
                / starting_price
                * 100
            )

            symbol_returns.append(
                symbol_return
            )

        return (
            sum(symbol_returns)
            / len(symbol_returns)
        )