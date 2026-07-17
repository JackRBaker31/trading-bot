import logging
import time
from collections.abc import Callable
from datetime import (
    datetime,
    timezone,
)

from app.active_order_manager import (
    ActiveOrderManager,
)
from app.execution import (
    ExecutionService,
)
from app.market_data import (
    MarketDataProvider,
)
from app.market_session import (
    MarketSession,
)
from app.news_analysis import (
    NewsAnalysis,
)
from app.news_analysis_provider import (
    NewsAnalysisProvider,
)
from app.news_policy_observation import (
    NewsPolicyObservation,
)
from app.news_policy_observation_log import (
    NewsPolicyObservationLog,
)
from app.news_trading_policy import (
    NewsTradingPolicy,
)
from app.orders import (
    Order,
    OrderSide,
)
from app.position_exit_manager import (
    PositionExitManager,
)
from app.position_state import (
    PositionState,
)
from app.strategy import (
    Strategy,
)
from app.position_state_store import (
    PositionStateStore,
)

logger = logging.getLogger(__name__)


class TradingLoop:
    def __init__(
        self,
        symbols: list[str],
        market_data: MarketDataProvider,
        strategy: Strategy,
        execution_service: ExecutionService,
        interval_seconds: float = 1.0,
        news_trading_policy: (
            NewsTradingPolicy | None
        ) = None,
        news_analysis_provider: (
            NewsAnalysisProvider | None
        ) = None,
        market_session: (
            MarketSession | None
        ) = None,
        enforce_market_hours: bool = False,
        active_order_manager: (
            ActiveOrderManager | None
        ) = None,
        refresh_active_orders_on_first_cycle: bool = True,
        news_policy_observation_log: (
            NewsPolicyObservationLog | None
        ) = None,
        news_policy_shadow_mode: bool = False,
        now_provider: (
            Callable[[], datetime] | None
        ) = None,
        position_exit_manager: (
            PositionExitManager | None
        ) = None,
        position_state_store: (
            PositionStateStore | None
        ) = None,
        position_states: (
            dict[str, PositionState] | None
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
        self.execution_service = (
            execution_service
        )
        self.interval_seconds = (
            interval_seconds
        )
        self.news_trading_policy = (
            news_trading_policy
            if news_trading_policy is not None
            else NewsTradingPolicy()
        )
        self.news_analysis_provider = (
            news_analysis_provider
        )
        self.market_session = market_session
        self.enforce_market_hours = (
            enforce_market_hours
        )
        self.active_order_manager = (
            active_order_manager
        )
        self.news_policy_observation_log = (
            news_policy_observation_log
        )
        self.news_policy_shadow_mode = (
            news_policy_shadow_mode
        )
        self.now_provider = (
            now_provider
            if now_provider is not None
            else lambda: datetime.now(
                timezone.utc
            )
        )
        self.refresh_active_orders_on_first_cycle = (
            refresh_active_orders_on_first_cycle
        )
        self.position_exit_manager = (
            position_exit_manager
        )
        self.position_state_store = (
            position_state_store
        )
        self.position_states = (
            position_states
            if position_states is not None
            else {}
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
        news_analysis_by_symbol: (
            dict[str, NewsAnalysis] | None
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

            if (
                self.active_order_manager
                is not None
                and (
                    cycle_number > 1
                    or self
                    .refresh_active_orders_on_first_cycle
                )
            ):
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

                    if (
                        self.position_exit_manager
                        is not None
                        and self.position_states
                    ):
                        exit_orders = (
                            self.position_exit_manager
                            .generate_exit_orders(
                                positions=self.position_states,
                                current_prices=current_prices,
                            )
                        )

                        orders.extend(
                            exit_orders
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

                    should_skip = (
                        self._should_skip_for_news(
                            order=order,
                            news_analysis_by_symbol=(
                                news_analysis_by_symbol
                            ),
                        )
                    )

                    if should_skip:
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

                    if (
                        executed
                        and order.side is OrderSide.BUY
                    ):
                        existing_state = (
                            self.position_states.get(
                                order.symbol
                            )
                        )

                        if existing_state is None:
                            self.position_states[
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

                    if (
                        executed
                        and order.side is OrderSide.SELL
                        and order.symbol
                        not in self.execution_service
                        .portfolio.positions
                    ):
                        self.position_states.pop(
                            order.symbol,
                            None,
                        )

                    if (
                        executed
                        and self.position_state_store
                        is not None
                    ):
                        self.position_state_store.save(
                            self.position_states
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

    def _should_skip_for_news(
        self,
        *,
        order: Order,
        news_analysis_by_symbol: (
            dict[str, NewsAnalysis] | None
        ),
    ) -> bool:
        analysis = None
        stored_analysis = None

        if news_analysis_by_symbol is not None:
            analysis = news_analysis_by_symbol.get(
                order.symbol
            )

        if (
            analysis is None
            and self.news_analysis_provider
            is not None
        ):
            get_stored_analysis = getattr(
                self.news_analysis_provider,
                "get_stored_analysis",
                None,
            )

            if get_stored_analysis is not None:
                stored_analysis = (
                    get_stored_analysis(
                        order.symbol
                    )
                )

                if stored_analysis is not None:
                    analysis = (
                        stored_analysis.analysis
                    )
            else:
                analysis = (
                    self.news_analysis_provider
                    .get_analysis(
                        order.symbol
                    )
                )

        if analysis is None:
            if (
                self.news_policy_observation_log
                is not None
            ):
                self.news_policy_observation_log.append(
                    NewsPolicyObservation(
                        symbol=order.symbol,
                        side=order.side,
                        quantity=order.quantity,
                        analysis_available=False,
                        analysis_sentiment=None,
                        analysis_expires_at=None,
                        would_approve=True,
                        reason=(
                            "No current news analysis "
                            "was available."
                        ),
                        observed_at=(
                            self.now_provider()
                        ),
                    )
                )

            return False

        approved = (
            self.news_trading_policy
            .approve_order(
                order=order,
                analysis=analysis,
            )
        )

        reason = self._news_policy_reason(
            approved=approved
        )

        if (
            self.news_policy_observation_log
            is not None
        ):
            self.news_policy_observation_log.append(
                NewsPolicyObservation(
                    symbol=order.symbol,
                    side=order.side,
                    quantity=order.quantity,
                    analysis_available=True,
                    analysis_sentiment=(
                        analysis.sentiment
                    ),
                    analysis_expires_at=(
                        stored_analysis.expires_at
                        if stored_analysis is not None
                        else None
                    ),
                    would_approve=approved,
                    reason=reason,
                    observed_at=(
                        self.now_provider()
                    ),
                )
            )

        if approved:
            return False

        if self.news_policy_shadow_mode:
            logger.info(
                "news_policy_shadow_rejection "
                "symbol=%s side=%s quantity=%s "
                "sentiment=%s impact_scope=%s",
                order.symbol,
                order.side.value,
                order.quantity,
                analysis.sentiment.value,
                analysis.impact_scope.value,
            )

            return False

        logger.warning(
            "order_skipped_news_policy "
            "symbol=%s side=%s "
            "quantity=%s sentiment=%s "
            "impact_scope=%s",
            order.symbol,
            order.side.value,
            order.quantity,
            analysis.sentiment.value,
            analysis.impact_scope.value,
        )

        print(
            "Result: SKIPPED "
            "(news policy rejected order)"
        )

        return True

    @staticmethod
    def _news_policy_reason(
        *,
        approved: bool,
    ) -> str:
        if approved:
            return (
                "News policy approved the order."
            )

        return (
            "Negative stock-specific news "
            "blocks BUY orders."
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