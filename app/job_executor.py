from typing import Any, Mapping

from app.config import load_config
from app.job import JobRecord, JobType
from app.market_data_factory import (
    create_market_data_provider,
)
from app.news_research_cycle_service import (
    NewsResearchCycleRequest,
    NewsResearchCycleService,
)
from app.research_report_service import (
    ResearchReportRequest,
    ResearchReportService,
)
from app.run_history_repository import (
    RunHistoryRepository,
)
from app.run_history_service import (
    RunHistoryService,
)
from app.shadow_decision_repository import (
    ShadowDecisionRepository,
)
from app.shadow_trading_service import ShadowTradingService
from app.intelligence_service import IntelligenceService
from app.system_status_service import SystemStatusService
from app.research_query_service import ResearchQueryService
from app.operations_query_service import OperationsQueryService
from app.paper_trading_process_controller import PaperTradingProcessController
from app.run_news_observation import (
    create_service as create_observation_service,
)
from app.watchlist_loader import load_watchlist


class JobExecutor:
    def __init__(
        self,
        *,
        application_database_path: str = (
            "data/application.db"
        ),
    ) -> None:
        self._application_database_path = (
            application_database_path
        )

    def execute(
        self,
        *,
        job: JobRecord,
    ) -> tuple[dict[str, object], bool]:
        if job.job_type == JobType.NEWS_RESEARCH_CYCLE:
            return self._execute_news_cycle(job.payload)

        if job.job_type == JobType.STRATEGY_REPORT:
            return self._execute_strategy_report(job.payload)

        if job.job_type == JobType.SHADOW_ANALYSIS:
            return self._execute_shadow_analysis(job.payload)

        raise ValueError(
            f"Unsupported job type: {job.job_type.value}."
        )

    def _create_run_history_service(
        self,
    ) -> RunHistoryService:
        service = RunHistoryService(
            repository=RunHistoryRepository(
                database_path=(
                    self._application_database_path
                )
            )
        )
        service.initialize()
        return service

    def _execute_news_cycle(
        self,
        payload: Mapping[str, Any],
    ) -> tuple[dict[str, object], bool]:
        symbols = self._resolve_symbols(payload)
        provider = str(
            payload.get("provider", "TWELVE_DATA")
        )
        max_price_requests = int(
            payload.get("max_price_requests", 5)
        )

        service = NewsResearchCycleService(
            observation_service_factory=(
                lambda store_path: (
                    create_observation_service(
                        store_path=store_path
                    )
                )
            ),
            market_data_provider_factory=(
                lambda provider_name, requested_symbols: (
                    create_market_data_provider(
                        provider_name=provider_name,
                        symbols=requested_symbols,
                    )
                )
            ),
            run_history_service=(
                self._create_run_history_service()
            ),
        )

        result = service.run(
            request=NewsResearchCycleRequest(
                symbols=tuple(symbols),
                provider_name=provider,
                max_price_requests=max_price_requests,
            )
        )

        snapshot = result.snapshot_summary
        outcome = result.outcome_summary
        failure_count = (
            (0 if snapshot is None else snapshot.failed_count)
            + (0 if outcome is None else outcome.failed_count)
        )

        return (
            {
                "provider": result.provider_name,
                "symbols": list(result.symbols),
                "articles_fetched": (
                    result.observation_summary.article_count
                ),
                "signals_stored": (
                    result.observation_summary.signal_count
                ),
                "snapshots_captured": (
                    0
                    if snapshot is None
                    else snapshot.captured_count
                ),
                "outcomes_recorded": (
                    0
                    if outcome is None
                    else outcome.recorded_count
                ),
                "failure_count": failure_count,
                "stale_outcomes_deferred": (
                    0
                    if outcome is None
                    else outcome.stale_quote_count
                ),
            },
            failure_count > 0,
        )

    def _execute_strategy_report(
        self,
        payload: Mapping[str, Any],
    ) -> tuple[dict[str, object], bool]:
        del payload
        config = load_config()

        result = ResearchReportService(
            run_history_service=(
                self._create_run_history_service()
            )
        ).run(
            request=ResearchReportRequest(
                starting_cash=config.starting_cash,
                max_order_value=(
                    config.risk.max_order_value
                ),
                max_position_value=(
                    config.risk.max_position_value
                ),
                max_portfolio_exposure=(
                    config.risk.max_portfolio_exposure
                ),
                target_allocation_percent=(
                    config.strategy
                    .target_allocation_percent
                ),
            )
        )

        return (
            {
                "strategy_name": result.report.strategy_name,
                "verdict": result.report.verdict,
                "completed_trades": (
                    result.report.net_completed_trades
                ),
                "json_path": result.artifacts.json_path,
                "csv_path": result.artifacts.csv_path,
            },
            False,
        )

    @staticmethod

    def _execute_shadow_analysis(
        self,
        payload: Mapping[str, Any],
    ) -> tuple[dict[str, object], bool]:
        del payload
        service = ShadowTradingService(
            intelligence_service=IntelligenceService(
                system_status_service=SystemStatusService(),
                research_query_service=ResearchQueryService(),
                operations_query_service=OperationsQueryService(),
                paper_trading_controller=PaperTradingProcessController(),
            ),
            repository=ShadowDecisionRepository(
                database_path=self._application_database_path
            ),
        )
        service.initialize()
        result = service.run_analysis()
        return result.to_dictionary(), False

    def _resolve_symbols(
        payload: Mapping[str, Any],
    ) -> list[str]:
        watchlist = payload.get("watchlist")

        if watchlist is not None:
            return load_watchlist(
                file_path=str(watchlist)
            )

        raw_symbols = payload.get("symbols")

        if not isinstance(raw_symbols, list):
            raise ValueError(
                "News job requires symbols or a watchlist."
            )

        symbols = [
            str(symbol).upper().strip()
            for symbol in raw_symbols
            if str(symbol).strip()
        ]

        if not symbols:
            raise ValueError(
                "News job requires at least one symbol."
            )

        return list(dict.fromkeys(symbols))
