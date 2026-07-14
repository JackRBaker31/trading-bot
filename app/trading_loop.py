import logging
import time
from collections.abc import Callable

from app.active_order_manager import (
    ActiveOrderManager,
)
from app.execution import ExecutionService
from app.market_data import MarketDataProvider
from app.market_session import MarketSession
from app.strategy import Strategy


logger = logging.getLogger(__name__)


class TradingLoop:
    def __init__(
        self,
        symbols: list[str],
        market_data: MarketDataProvider,
        strategy: Strategy,
        execution_service: ExecutionService,
        interval_seconds: float = 1.0,
        market_session: MarketSession | None = None,
        enforce_market_hours: bool = False,
        active_order_manager: (
            ActiveOrderManager | None
        ) = None,
    ) -> None:
        if not symbols:
            raise ValueError(
                "At least one symbol is required."
            )

        if interval_seconds < 0:
            raise ValueError(
                "Interval cannot be negative."
            )

        self.symbols = [
            symbol.upper().strip()
            for symbol in symbols
        ]

        self.market_data = market_data
        self.strategy = strategy
        self.execution_service = execution_service
        self.interval_seconds = interval_seconds
        self.market_session = market_session
        self.enforce_market_hours = (
            enforce_market_hours
        )
        self.active_order_manager = (
            active_order_manager
        )

    def run(
        self,
        cycles: int | None,
        before_cycle: (
            Callable[[int], None] | None
        ) = None,
        stop_requested: (
            Callable[[], bool] | None
        ) = None,
    ) -> None:
        if (
            cycles is not None
            and cycles <= 0
        ):
            raise ValueError(
                "Cycles must be greater than zero."
            )

        cycle_description = (
            str(cycles)
            if cycles is not None
            else "continuous"
        )

        logger.info(
            "trading_loop_started "
            "cycles=%s interval_seconds=%s "
            "symbols=%s",
            cycle_description,
            self.interval_seconds,
            ",".join(self.symbols),
        )

        if cycles is None:
            print(
                "\nStarting continuous trading loop..."
            )
        else:
            print(
                "\nStarting trading loop for "
                f"{cycles} cycles..."
            )

        cycle_number = 1
        cycles_completed = 0

        while True:
            if (
                cycles is not None
                and cycle_number > cycles
            ):
                break

            if (
                stop_requested is not None
                and stop_requested()
            ):
                break

            logger.info(
                "trading_cycle_started cycle=%s",
                cycle_number,
            )

            print(
                f"\n--- CYCLE {cycle_number} ---"
            )

            if self.active_order_manager is not None:
                self.active_order_manager.refresh()

                logger.info(
                    "active_orders_refreshed "
                    "cycle=%s active_order_count=%s",
                    cycle_number,
                    len(
                        self.active_order_manager
                        .active_orders
                    ),
                )

            if before_cycle is not None:
                before_cycle(
                    cycle_number
                )

            skip_trading = False

            if self.enforce_market_hours:
                if self.market_session is None:
                    raise RuntimeError(
                        "Market-hours enforcement is "
                        "enabled but no market session "
                        "was supplied."
                    )

                session_status = (
                    self.market_session.get_status()
                )

                logger.info(
                    "market_session_checked "
                    "cycle=%s is_open=%s reason=%s "
                    "local_time=%s",
                    cycle_number,
                    session_status.is_open,
                    session_status.reason,
                    (
                        session_status
                        .local_time
                        .isoformat()
                    ),
                )

                if not session_status.is_open:
                    skip_trading = True

                    print(
                        "Trading skipped: "
                        f"{session_status.reason}"
                    )

                    logger.warning(
                        "trading_cycle_skipped "
                        "cycle=%s reason=%s",
                        cycle_number,
                        session_status.reason,
                    )

            if not skip_trading:
                try:
                    current_prices = (
                        self.market_data.get_prices(
                            self.symbols
                        )
                    )
                except Exception:
                    logger.exception(
                        "market_data_error cycle=%s",
                        cycle_number,
                    )
                    raise

                logger.info(
                    "prices_received "
                    "cycle=%s prices=%s",
                    cycle_number,
                    current_prices,
                )

                self._display_prices(
                    current_prices
                )

                try:
                    orders = (
                        self.strategy.generate_orders(
                            prices=current_prices,
                            portfolio=(
                                self.execution_service
                                .portfolio
                            ),
                        )
                    )
                except Exception:
                    logger.exception(
                        "strategy_error cycle=%s",
                        cycle_number,
                    )
                    raise

                logger.info(
                    "strategy_completed "
                    "cycle=%s order_count=%s",
                    cycle_number,
                    len(orders),
                )

                if not orders:
                    print(
                        "No orders generated."
                    )
                else:
                    print(
                        "Orders generated: "
                        f"{len(orders)}"
                    )

                for order in orders:
                    print(
                        "Strategy proposed: "
                        f"{order.side.value} "
                        f"{order.quantity} "
                        f"{order.symbol} "
                        f"at £{order.price:.2f}"
                    )

                    if (
                        self.active_order_manager
                        is not None
                        and self.active_order_manager
                        .is_symbol_blocked(
                            order.symbol
                        )
                    ):
                        logger.warning(
                            "order_skipped_active_"
                            "broker_order "
                            "symbol=%s side=%s "
                            "quantity=%s",
                            order.symbol,
                            order.side.value,
                            order.quantity,
                        )

                        print(
                            "Result: SKIPPED "
                            "(active broker order "
                            "exists)"
                        )

                        continue

                    executed = (
                        self.execution_service
                        .submit_order(
                            order=order,
                            current_prices=(
                                current_prices
                            ),
                        )
                    )

                    result = (
                        "EXECUTED"
                        if executed
                        else "REJECTED"
                    )

                    print(
                        f"Result: {result}"
                    )

            logger.info(
                "trading_cycle_completed cycle=%s",
                cycle_number,
            )

            cycles_completed += 1
            cycle_number += 1

            if (
                cycles is not None
                and cycles_completed >= cycles
            ):
                break

            if (
                stop_requested is not None
                and stop_requested()
            ):
                break

            time.sleep(
                self.interval_seconds
            )

        logger.info(
            "trading_session_finished "
            "cycles_completed=%s "
            "symbol_count=%s",
            cycles_completed,
            len(self.symbols),
        )

        print(
            "\nTrading loop finished."
        )

    @staticmethod
    def _display_prices(
        current_prices: dict[str, float],
    ) -> None:
        print(
            "Current prices:"
        )

        for symbol, price in (
            current_prices.items()
        ):
            print(
                f"  {symbol}: £{price:.2f}"
            )