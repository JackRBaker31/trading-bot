from collections import defaultdict

from app.backtest_models import (
    BacktestResult,
    HistoricalPriceBar,
)
from app.execution import (
    ExecutionService,
)
from app.portfolio import (
    Portfolio,
)
from app.risk import (
    RiskEngine,
    RiskLimits,
)
from app.strategy import (
    Strategy,
)
from app.trade_log import (
    TradeLog,
)
from pathlib import Path
from app.completed_trade_tracker import (
    CompletedTradeTracker,
)
from app.orders import (
    OrderSide,
)

class BacktestEngine:
    def __init__(
        self,
        *,
        strategy: Strategy,
        starting_cash: float,
        trade_log_path: Path | None = None,
    ) -> None:
        if starting_cash <= 0:
            raise ValueError(
                "Starting cash must be positive."
            )

        self._strategy = strategy
        self._starting_cash = starting_cash
        self._trade_log_path = (
            trade_log_path
            if trade_log_path is not None
            else Path(
                "data/backtest_trade_log.jsonl"
            )
        )

    def run(
        self,
        *,
        bars: list[HistoricalPriceBar],
    ) -> BacktestResult:
        if not bars:
            raise ValueError(
                "Backtest bars are required."
            )

        bars_by_date: dict[
            object,
            list[HistoricalPriceBar],
        ] = defaultdict(list)

        for bar in bars:
            bars_by_date[
                bar.trading_date
            ].append(bar)

        portfolio = Portfolio(
            starting_cash=self._starting_cash,
        )

        trade_log = TradeLog(
            file_path=self._trade_log_path,
        )

        approved_symbols = {
            bar.symbol
            for bar in bars
        }

        risk_engine = RiskEngine(
            limits=RiskLimits(
                max_order_value=(
                    self._starting_cash
                ),
                max_position_value=(
                    self._starting_cash
                ),
                max_portfolio_exposure=1.0,
                max_trades_per_session=10_000,
                approved_symbols=(
                    approved_symbols
                ),
            )
        )

        execution_service = (
            ExecutionService(
                portfolio=portfolio,
                risk_engine=risk_engine,
                trade_log=trade_log,
            )
        )

        trade_tracker = (
            CompletedTradeTracker()
        )

        latest_prices: dict[
            str,
            float,
        ] = {}

        trade_count = 0
        peak_value = self._starting_cash
        maximum_drawdown_percent = 0.0

        for trading_date in sorted(
            bars_by_date
        ):
            daily_prices = {
                bar.symbol: bar.close_price
                for bar in bars_by_date[
                    trading_date
                ]
            }

            latest_prices.update(
                daily_prices
            )

            orders = (
                self._strategy.generate_orders(
                    prices=daily_prices,
                    portfolio=portfolio,
                )
            )

            for order in orders:
                executed = (
                    execution_service.submit_order(
                        order=order,
                        current_prices=(
                            daily_prices
                        ),
                    )
                )

                if executed:
                    trade_count += 1

                    if order.side is OrderSide.BUY:
                        trade_tracker.record_buy(
                            symbol=order.symbol,
                            quantity=order.quantity,
                            price=order.price,
                        )
                    else:
                        trade_tracker.record_sell(
                            symbol=order.symbol,
                            quantity=order.quantity,
                            price=order.price,
                        )

            portfolio_value = (
                portfolio.cash
                + sum(
                    quantity
                    * latest_prices.get(
                        symbol,
                        0.0,
                    )
                    for symbol, quantity
                    in portfolio.positions.items()
                )
            )

            peak_value = max(
                peak_value,
                portfolio_value,
            )

            if peak_value > 0:
                drawdown_percent = (
                    (
                        peak_value
                        - portfolio_value
                    )
                    / peak_value
                    * 100.0
                )

                maximum_drawdown_percent = max(
                    maximum_drawdown_percent,
                    drawdown_percent,
                )

        ending_value = (
            portfolio.cash
            + sum(
                quantity
                * latest_prices.get(
                    symbol,
                    0.0,
                )
                for symbol, quantity
                in portfolio.positions.items()
            )
        )

        return BacktestResult(
            starting_cash=self._starting_cash,
            ending_value=ending_value,
            trade_count=trade_count,
            winning_trade_count=(
                trade_tracker
                .winning_trade_count
            ),
            losing_trade_count=(
                trade_tracker
                .losing_trade_count
            ),
            maximum_drawdown_percent=(
                maximum_drawdown_percent
            ),
        )