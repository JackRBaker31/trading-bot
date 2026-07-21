import logging
from collections.abc import Callable

from app.application_errors import TradingOperationError
from app.run_history import RunType
from app.run_history_service import RunHistoryService
from app.trading_application import (
    TradingApplicationRequest,
    TradingApplicationResult,
)
from app.trading_application_factory import (
    TradingApplicationRuntimeFactory,
)


logger = logging.getLogger(__name__)


class TradingApplicationService:
    def __init__(
        self,
        *,
        runtime_factory: (
            TradingApplicationRuntimeFactory | None
        ) = None,
        run_history_service: RunHistoryService | None = None,
    ) -> None:
        self._runtime_factory = (
            runtime_factory
            or TradingApplicationRuntimeFactory()
        )
        self._run_history_service = run_history_service

    def run(
        self,
        *,
        request: TradingApplicationRequest,
        stop_requested: Callable[[], bool] | None = None,
    ) -> TradingApplicationResult:
        runtime = self._runtime_factory.build(
            config_path=request.config_path
        )
        config = runtime.config

        if request.require_paper_mode and config.mode != "PAPER":
            raise TradingOperationError(
                "The paper-trading worker requires PAPER mode.",
                code="PAPER_MODE_REQUIRED",
                context={"mode": config.mode},
            )

        history_record = None
        if (
            config.mode == "PAPER"
            and self._run_history_service is not None
        ):
            history_record = self._run_history_service.start_run(
                run_type=RunType.PAPER_TRADING_STARTUP,
                provider=config.market_data_provider,
                symbols=tuple(config.symbols),
                metadata={
                    "config_path": request.config_path,
                    "cycles": config.trading_loop.cycles,
                },
            )

        try:
            result = self._run_runtime(
                runtime=runtime,
                stop_requested=stop_requested,
            )
        except Exception as error:
            if (
                history_record is not None
                and self._run_history_service is not None
            ):
                self._run_history_service.fail_run(
                    run_id=history_record.run_id,
                    error=error,
                )
            raise

        if (
            history_record is not None
            and self._run_history_service is not None
        ):
            if result.trading_started:
                self._run_history_service.complete_run(
                    run_id=history_record.run_id,
                    created_count=(
                        result.executed_trade_count
                    ),
                    metadata={
                        "reason": result.reason,
                        "cash": result.cash,
                        "position_count": len(
                            result.positions
                        ),
                        "stopped_by_request": (
                            result.stopped_by_request
                        ),
                    },
                )
            else:
                self._run_history_service.fail_run(
                    run_id=history_record.run_id,
                    error=TradingOperationError(
                        result.reason,
                        code="PAPER_STARTUP_REFUSED",
                    ),
                )

        return result

    def _run_runtime(
        self,
        *,
        runtime,
        stop_requested: Callable[[], bool] | None,
    ) -> TradingApplicationResult:
        config = runtime.config

        logger.info(
            "application_starting mode=%s provider=%s",
            config.mode,
            config.market_data_provider,
        )

        print("Trading system starting...")
        print(f"Mode: {config.mode}")
        print(
            "Market data: "
            f"{config.market_data_provider}"
        )
        print("Real-money trading: DISABLED")

        trading_started = False
        reason = "Trading completed."

        def start_trading() -> None:
            nonlocal trading_started
            trading_started = True
            runtime.trading_loop.run(
                cycles=config.trading_loop.cycles,
                before_cycle=runtime.prepare_cycle,
                stop_requested=stop_requested,
            )

        if config.mode == "PAPER":
            if runtime.paper_startup_service is None:
                raise RuntimeError(
                    "PAPER startup service was not initialized."
                )
            if runtime.historical_fill_importer is None:
                raise RuntimeError(
                    "Historical fill importer was not initialized."
                )

            historical_fill_result = (
                runtime.historical_fill_importer
                .import_unapplied_fills()
            )
            logger.info(
                "historical_fill_import_completed "
                "imported_order_ids=%s skipped_order_ids=%s",
                historical_fill_result.imported_order_ids,
                historical_fill_result.skipped_order_ids,
            )

            startup_result = runtime.paper_startup_service.start(
                start_trading=start_trading
            )
            reason = startup_result.reason

            if runtime.startup_summary_builder is not None:
                startup_summary = (
                    runtime.startup_summary_builder.build(
                        startup_result=startup_result
                    )
                )
                logger.info(
                    "paper_startup_summary outcome=%s "
                    "startup_approved=%s",
                    startup_summary.outcome.value,
                    startup_summary.startup_approved,
                )

            if not startup_result.trading_started:
                print(
                    "Trading refused: "
                    f"{startup_result.reason}"
                )
                return TradingApplicationResult(
                    mode=config.mode,
                    trading_started=False,
                    reason=startup_result.reason,
                    stopped_by_request=False,
                    cash=runtime.portfolio.cash,
                    positions=dict(
                        runtime.portfolio.positions
                    ),
                    executed_trade_count=(
                        runtime.risk_engine
                        .executed_trade_count
                    ),
                )
        else:
            start_trading()

        runtime.portfolio_store.save(runtime.portfolio)
        runtime.position_state_store.save(
            runtime.trading_loop.position_states
        )

        final_prices = runtime.market_data.get_prices(
            config.symbols
        )
        runtime.portfolio.display(final_prices)
        runtime.trade_log.display()

        stopped = (
            stop_requested is not None
            and stop_requested()
        )

        logger.info(
            "application_finished cash=%.2f positions=%s "
            "session_trade_count=%s stopped=%s",
            runtime.portfolio.cash,
            runtime.portfolio.positions,
            runtime.risk_engine.executed_trade_count,
            stopped,
        )

        return TradingApplicationResult(
            mode=config.mode,
            trading_started=trading_started,
            reason=reason,
            stopped_by_request=stopped,
            cash=runtime.portfolio.cash,
            positions=dict(runtime.portfolio.positions),
            executed_trade_count=(
                runtime.risk_engine.executed_trade_count
            ),
        )
