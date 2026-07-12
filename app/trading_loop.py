import logging
import time
from collections.abc import Callable

from app.execution import ExecutionService
from app.market_data import MarketDataProvider
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
    ) -> None:
        if not symbols:
            raise ValueError("At least one symbol is required.")

        if interval_seconds < 0:
            raise ValueError("Interval cannot be negative.")

        self.symbols = [
            symbol.upper().strip()
            for symbol in symbols
        ]

        self.market_data = market_data
        self.strategy = strategy
        self.execution_service = execution_service
        self.interval_seconds = interval_seconds

    def run(
        self,
        cycles: int,
        before_cycle: Callable[[int], None] | None = None,
    ) -> None:
        if cycles <= 0:
            raise ValueError("Cycles must be greater than zero.")

        logger.info(
            "trading_loop_started cycles=%s interval_seconds=%s symbols=%s",
            cycles,
            self.interval_seconds,
            ",".join(self.symbols),
        )

        print(f"\nStarting trading loop for {cycles} cycles...")

        for cycle_number in range(1, cycles + 1):
            logger.info(
                "trading_cycle_started cycle=%s",
                cycle_number,
            )

            print(f"\n--- CYCLE {cycle_number} ---")

            if before_cycle is not None:
                before_cycle(cycle_number)

            try:
                current_prices = self.market_data.get_prices(
                    self.symbols
                )
            except Exception:
                logger.exception(
                    "market_data_error cycle=%s",
                    cycle_number,
                )
                raise

            logger.info(
                "prices_received cycle=%s prices=%s",
                cycle_number,
                current_prices,
            )

            self._display_prices(current_prices)

            try:
                orders = self.strategy.generate_orders(
                    current_prices
                )
            except Exception:
                logger.exception(
                    "strategy_error cycle=%s",
                    cycle_number,
                )
                raise

            logger.info(
                "strategy_completed cycle=%s order_count=%s",
                cycle_number,
                len(orders),
            )

            if not orders:
                print("No orders generated.")
            else:
                print(f"Orders generated: {len(orders)}")

            for order in orders:
                print(
                    f"Strategy proposed: "
                    f"{order.side.value} "
                    f"{order.quantity} {order.symbol} "
                    f"at £{order.price:.2f}"
                )

                executed = self.execution_service.submit_order(
                    order=order,
                    current_prices=current_prices,
                )

                result = "EXECUTED" if executed else "REJECTED"
                print(f"Result: {result}")

            logger.info(
                "trading_cycle_completed cycle=%s",
                cycle_number,
            )

            if cycle_number < cycles:
                time.sleep(self.interval_seconds)

        logger.info(
            "trading_loop_finished cycles=%s",
            cycles,
        )

        print("\nTrading loop finished.")

    @staticmethod
    def _display_prices(
        current_prices: dict[str, float],
    ) -> None:
        print("Current prices:")

        for symbol, price in current_prices.items():
            print(f"  {symbol}: £{price:.2f}")