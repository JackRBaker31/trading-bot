from app.infrastructure_status_service import (
    InfrastructureStatusService,
)
from app.worker_heartbeat_repository import (
    WorkerHeartbeatRepository,
)
from app.daily_briefing_service import DailyBriefingService
from app.intelligence_graduation_service import (
    IntelligenceGraduationService,
)
from app.shadow_performance_service import (
    ShadowPerformanceService,
)
from app.shadow_decision_repository import ShadowDecisionRepository
from app.shadow_trading_service import ShadowTradingService
from app.intelligence_service import IntelligenceService
from app.audit_service import AuditService
from app.auth_repository import AuthenticationRepository
from app.auth_service import AuthenticationService
from app.paper_trading_process_controller import (
    PaperTradingProcessController,
)
from app.operations_query_service import (
    OperationsQueryService,
)
from app.job_repository import (
    JobRepository,
)
from app.job_service import JobService
from app.research_query_service import (
    ResearchQueryService,
)
from app.run_history_repository import (
    RunHistoryRepository,
)
from app.run_history_service import (
    RunHistoryService,
)
from app.system_status_service import (
    SystemStatusService,
)
from app.scheduled_task_repository import ScheduledTaskRepository
from app.schedule_management_service import ScheduleManagementService
from app.copilot_service import CopilotService
from app.intelligence_observability_service import (
    IntelligenceObservabilityService,
)
from app.operation_diagnostics_repository import (
    OperationDiagnosticsRepository,
)
from app.operation_diagnostics_service import (
    OperationDiagnosticsService,
)
from app.advanced_intelligence_service import (
    AdvancedIntelligenceService,
)
from app.bayesian_confidence_service import (
    BayesianConfidenceService,
)
from app.explainable_decision_service import (
    ExplainableDecisionService,
)
from app.market_regime_service import (
    MarketRegimeService,
)
from app.multi_timeframe_service import (
    MultiTimeframeService,
)
from app.adaptive_intelligence_service import (
    AdaptiveIntelligenceService,
)
from app.investment_committee_service import (
    InvestmentCommitteeService,
)
from app.performance_intelligence_service import (
    PerformanceIntelligenceService,
)
from app.portfolio_optimisation_service import (
    PortfolioOptimisationService,
)
from app.position_sizing_service import (
    PositionSizingService,
)
from app.risk_attribution_service import (
    RiskAttributionService,
)
from app.strategy_evolution_repository import (
    StrategyEvolutionRepository,
)
from app.strategy_evolution_service import (
    StrategyEvolutionService,
)
from app.decision_outcome_repository import DecisionOutcomeRepository
from app.decision_outcome_service import DecisionOutcomeService
from app.decision_memory_repository import DecisionMemoryRepository
from app.decision_memory_service import DecisionMemoryService
from app.macro_analysis_service import MacroAnalysisService
from app.macro_capability_provider import MacroCapabilityProvider
from app.technical_analysis_service import TechnicalAnalysisService
from app.technical_capability_provider import TechnicalCapabilityProvider
from app.twelve_data_historical_data import TwelveDataHistoricalDataClient
from app.investment_capability_providers import (
    NewsCapabilityProvider,
    PortfolioCapabilityProvider,
    RiskCapabilityProvider,
    UnavailableCapabilityProvider,
)
from app.investment_thesis_service import InvestmentThesisService
from app.decision_engine_service import DecisionEngineService
from app.copilot_change_service import (
    CopilotChangeService,
)
from app.copilot_history_repository import (
    CopilotHistoryRepository,
)
from app.decision_intelligence_service import (
    DecisionIntelligenceService,
)
from app.decision_trace_repository import (
    DecisionTraceRepository,
)
from app.symbol_decision_history_service import (
    SymbolDecisionHistoryService,
)
from app.symbol_decision_repository import (
    SymbolDecisionRepository,
)
from app.symbol_decision_service import (
    SymbolDecisionService,
)

DEFAULT_APPLICATION_DATABASE_PATH = (
    "data/application.db"
)


def create_system_status_service(
) -> SystemStatusService:
    return SystemStatusService()


def create_run_history_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> RunHistoryService:
    return RunHistoryService(
        repository=RunHistoryRepository(
            database_path=database_path
        )
    )

def create_job_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> JobService:
    service = JobService(
        repository=JobRepository(
            database_path=database_path
        )
    )
    service.initialize()
    return service


def create_research_query_service(
) -> ResearchQueryService:
    return ResearchQueryService()


def create_operations_query_service(
) -> OperationsQueryService:
    return OperationsQueryService()



def create_paper_trading_controller(
) -> PaperTradingProcessController:
    return PaperTradingProcessController()



def create_authentication_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> AuthenticationService:
    repository = AuthenticationRepository(
        database_path=database_path
    )
    service = AuthenticationService(
        repository=repository
    )
    service.initialize()
    return service


def create_audit_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> AuditService:
    repository = AuthenticationRepository(
        database_path=database_path
    )
    repository.initialize()
    return AuditService(
        repository=repository
    )


def create_intelligence_service(
) -> IntelligenceService:
    return IntelligenceService(
        system_status_service=(
            create_system_status_service()
        ),
        research_query_service=(
            create_research_query_service()
        ),
        operations_query_service=(
            create_operations_query_service()
        ),
        paper_trading_controller=(
            create_paper_trading_controller()
        ),
    )


def create_shadow_trading_service(
    *,
    database_path: str = DEFAULT_APPLICATION_DATABASE_PATH,
) -> ShadowTradingService:
    service = ShadowTradingService(
        intelligence_service=create_intelligence_service(),
        repository=ShadowDecisionRepository(
            database_path=database_path
        ),
    )
    service.initialize()
    return service



def create_shadow_performance_service(
    *,
    database_path: str = DEFAULT_APPLICATION_DATABASE_PATH,
) -> ShadowPerformanceService:
    repository = ShadowDecisionRepository(
        database_path=database_path
    )
    repository.initialize()
    return ShadowPerformanceService(
        repository=repository
    )


def create_intelligence_graduation_service(
    *,
    database_path: str = DEFAULT_APPLICATION_DATABASE_PATH,
) -> IntelligenceGraduationService:
    return IntelligenceGraduationService(
        performance_service=(
            create_shadow_performance_service(
                database_path=database_path
            )
        ),
        intelligence_service=(
            create_intelligence_service()
        ),
    )


def create_daily_briefing_service(
) -> DailyBriefingService:
    return DailyBriefingService(
        intelligence_service=(
            create_intelligence_service()
        ),
        shadow_performance_service=(
            create_shadow_performance_service()
        ),
        graduation_service=(
            create_intelligence_graduation_service()
        ),
    )


def create_infrastructure_status_service(
    *,
    database_path: str = DEFAULT_APPLICATION_DATABASE_PATH,
) -> InfrastructureStatusService:
    repository = WorkerHeartbeatRepository(
        database_path=database_path
    )
    repository.initialize()
    return InfrastructureStatusService(
        heartbeat_repository=repository
    )


def create_schedule_management_service(
    *, database_path: str = DEFAULT_APPLICATION_DATABASE_PATH,
) -> ScheduleManagementService:
    service = ScheduleManagementService(
        repository=ScheduledTaskRepository(database_path=database_path),
        job_service=create_job_service(database_path=database_path),
    )
    service.initialize()
    return service

def create_copilot_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> CopilotService:
    return CopilotService(
        infrastructure_status_provider=(
            lambda: (
                create_infrastructure_status_service(
                    database_path=database_path
                ).get_status()
            )
        ),
        recent_jobs_provider=(
            lambda: (
                create_job_service(
                    database_path=database_path
                ).list_recent(
                    limit=100
                )
            )
        ),
        schedules_provider=(
            lambda: (
                create_schedule_management_service(
                    database_path=database_path
                ).list()
            )
        ),
        intelligence_snapshot_provider=(
            lambda: (
                create_intelligence_service()
                .get_snapshot()
                .to_dictionary()
            )
        ),
        graduation_status_provider=(
            lambda: (
                create_intelligence_graduation_service(
                    database_path=database_path
                )
                .get_status()
                .to_dictionary()
            )
        ),
    )
    
def create_intelligence_snapshot(
) -> dict[str, object]:
    """
    Temporary grounded provider.

    Next phase this becomes the real
    Intelligence Cycle snapshot.
    """

    return {
        "trading_readiness":
            "NOT_READY",

        "market_outlook":
            "NEUTRAL",

        "confidence":
            0.0,

        "signal_count":
            0,

        "actionable_signal_count":
            0,

        "evidence_quality":
            "UNKNOWN",
    }


def create_graduation_snapshot(
) -> dict[str, object]:
    """
    Temporary grounded provider.

    Next phase this connects directly
    to Shadow Trading.
    """

    return {
        "ready": False,
        "checks": [],
    }
    
def create_copilot_change_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> CopilotChangeService:
    service = CopilotChangeService(
        repository=CopilotHistoryRepository(
            database_path=database_path
        ),
        overview_provider=(
            lambda: (
                create_copilot_service(
                    database_path=database_path
                ).dashboard_overview()
            )
        ),
    )

    service.initialize()

    return service


def create_decision_intelligence_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> DecisionIntelligenceService:
    service = DecisionIntelligenceService(
        repository=DecisionTraceRepository(
            database_path=database_path
        ),
        overview_provider=(
            lambda: (
                create_copilot_service(
                    database_path=database_path
                ).dashboard_overview()
            )
        ),
    )

    service.initialize()

    return service


def create_symbol_decision_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> SymbolDecisionService:
    intelligence_service = (
        create_intelligence_service()
    )

    graduation_service = (
        create_intelligence_graduation_service(
            database_path=database_path
        )
    )

    service = SymbolDecisionService(
        repository=SymbolDecisionRepository(
            database_path=database_path
        ),
        snapshot_provider=(
            intelligence_service.get_snapshot
        ),
        graduation_provider=(
            graduation_service.get_status
        ),
    )

    service.initialize()

    return service


def create_symbol_decision_history_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> SymbolDecisionHistoryService:
    service = SymbolDecisionHistoryService(
        repository=SymbolDecisionRepository(
            database_path=database_path
        ),
    )

    service.initialize()

    return service


def create_decision_engine_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> DecisionEngineService:
    intelligence_service = (
        create_intelligence_service()
    )

    operations_service = (
        create_operations_query_service()
    )

    graduation_service = (
        create_intelligence_graduation_service(
            database_path=database_path
        )
    )

    return DecisionEngineService(
        snapshot_provider=(
            intelligence_service
            .get_snapshot
        ),
        risk_provider=(
            lambda: (
                operations_service
                .get_risk_status()
            )
        ),
        portfolio_provider=(
            lambda: (
                operations_service
                .get_portfolio()
            )
        ),
        graduation_provider=(
            graduation_service
            .get_status
        ),
    )



def create_investment_thesis_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> InvestmentThesisService:
    intelligence_service = (
        create_intelligence_service()
    )
    operations_service = (
        create_operations_query_service()
    )
    graduation_service = (
        create_intelligence_graduation_service(
            database_path=database_path
        )
    )

    return InvestmentThesisService(
        snapshot_provider=(
            intelligence_service
            .get_snapshot
        ),
        risk_provider=(
            operations_service
            .get_risk_status
        ),
        portfolio_provider=(
            operations_service
            .get_portfolio
        ),
        graduation_provider=(
            graduation_service
            .get_status
        ),
        capability_providers=(
            NewsCapabilityProvider(),
            TechnicalCapabilityProvider(
                bars_provider=(
                    lambda symbol, output_size: (
                        create_technical_historical_client()
                        .get_daily_bars(
                            symbol=symbol,
                            output_size=output_size,
                        )
                    )
                ),
                analysis_service=(
                    create_technical_analysis_service()
                ),
            ),
            create_macro_capability_provider(),
            UnavailableCapabilityProvider(
                capability="VALUATION",
                maximum=10.0,
                summary=(
                    "Valuation capability has "
                    "not yet been connected."
                ),
            ),
            PortfolioCapabilityProvider(),
            RiskCapabilityProvider(),
        ),
    )



def create_technical_historical_client(
) -> TwelveDataHistoricalDataClient:
    import os

    api_key = os.getenv(
        "TWELVE_DATA_API_KEY"
    )

    if (
        api_key is None
        or not api_key.strip()
    ):
        raise RuntimeError(
            "TWELVE_DATA_API_KEY was not "
            "found in the environment."
        )

    return TwelveDataHistoricalDataClient(
        api_key=api_key,
        timeout_seconds=15.0,
        max_attempts=2,
    )


def create_technical_analysis_service(
) -> TechnicalAnalysisService:
    return TechnicalAnalysisService()



def create_macro_analysis_service(
) -> MacroAnalysisService:
    return MacroAnalysisService()


def create_macro_capability_provider(
) -> MacroCapabilityProvider:
    return MacroCapabilityProvider(
        bars_provider=(
            lambda symbol, output_size: (
                create_technical_historical_client()
                .get_daily_bars(
                    symbol=symbol,
                    output_size=output_size,
                )
            )
        ),
        analysis_service=(
            create_macro_analysis_service()
        ),
    )



def create_decision_memory_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> DecisionMemoryService:
    service = DecisionMemoryService(
        repository=(
            DecisionMemoryRepository(
                database_path=database_path
            )
        ),
    )
    service.initialize()
    return service



def create_decision_outcome_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> DecisionOutcomeService:
    memory_service = (
        create_decision_memory_service(
            database_path=database_path
        )
    )

    service = DecisionOutcomeService(
        repository=(
            DecisionOutcomeRepository(
                database_path=database_path
            )
        ),
        decisions_provider=(
            lambda limit: (
                memory_service.recent(
                    limit=limit
                )
            )
        ),
        bars_provider=(
            lambda symbol, output_size: (
                create_technical_historical_client()
                .get_daily_bars(
                    symbol=symbol,
                    output_size=output_size,
                )
            )
        ),
    )
    service.initialize()
    return service



def create_adaptive_intelligence_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> AdaptiveIntelligenceService:
    memory_service = (
        create_decision_memory_service(
            database_path=database_path
        )
    )
    outcome_service = (
        create_decision_outcome_service(
            database_path=database_path
        )
    )
    thesis_service = (
        create_investment_thesis_service(
            database_path=database_path
        )
    )
    operations_service = (
        create_operations_query_service()
    )

    performance_service = (
        PerformanceIntelligenceService()
    )
    evolution_service = (
        StrategyEvolutionService(
            repository=(
                StrategyEvolutionRepository(
                    database_path=database_path
                )
            )
        )
    )
    evolution_service.initialize()

    return AdaptiveIntelligenceService(
        decisions_provider=(
            lambda: tuple(
                item.to_dictionary()
                for item
                in memory_service.recent(
                    limit=500
                )
            )
        ),
        outcomes_provider=(
            lambda: tuple(
                item.to_dictionary()
                for item
                in outcome_service
                .overview(
                    limit=1000
                )
                .latest
            )
        ),
        theses_provider=(
            lambda: tuple(
                item.to_dictionary()
                for item
                in thesis_service
                .get_report()
                .theses
            )
        ),
        portfolio_provider=(
            lambda: (
                operations_service
                .get_portfolio()
                .to_dictionary()
            )
        ),
        risk_provider=(
            lambda: (
                operations_service
                .get_risk_status()
                .to_dictionary()
            )
        ),
        performance_service=(
            performance_service
        ),
        portfolio_service=(
            PortfolioOptimisationService()
        ),
        risk_service=(
            RiskAttributionService()
        ),
        sizing_service=(
            PositionSizingService(
                performance_service=(
                    performance_service
                )
            )
        ),
        committee_service=(
            InvestmentCommitteeService()
        ),
        evolution_service=(
            evolution_service
        ),
    )



def create_advanced_intelligence_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> AdvancedIntelligenceService:
    thesis_service = (
        create_investment_thesis_service(
            database_path=database_path
        )
    )
    outcome_service = (
        create_decision_outcome_service(
            database_path=database_path
        )
    )

    def bars(
        symbol: str,
        output_size: int,
    ):
        return (
            create_technical_historical_client()
            .get_daily_bars(
                symbol=symbol,
                output_size=output_size,
            )
        )

    def aggregate(
        daily_bars,
        group_size: int,
    ):
        grouped = []

        for index in range(
            0,
            len(daily_bars),
            group_size,
        ):
            chunk = daily_bars[
                index:index + group_size
            ]

            if not chunk:
                continue

            grouped.append(
                type(chunk[0])(
                    symbol=chunk[0].symbol,
                    trading_date=(
                        chunk[-1].trading_date
                    ),
                    open_price=(
                        chunk[0].open_price
                    ),
                    high_price=max(
                        item.high_price
                        for item in chunk
                    ),
                    low_price=min(
                        item.low_price
                        for item in chunk
                    ),
                    close_price=(
                        chunk[-1].close_price
                    ),
                    volume=sum(
                        item.volume
                        for item in chunk
                    ),
                )
            )

        return grouped

    def timeframe_series(
        symbol: str,
    ):
        daily = bars(
            symbol,
            500,
        )

        return {
            "MONTHLY": aggregate(
                daily,
                21,
            ),
            "WEEKLY": aggregate(
                daily,
                5,
            ),
            "DAILY": daily,
        }

    return AdvancedIntelligenceService(
        regime_series_provider=(
            lambda: {
                symbol: bars(
                    symbol,
                    260,
                )
                for symbol in (
                    "SPY",
                    "QQQ",
                    "TLT",
                )
            }
        ),
        timeframe_series_provider=(
            timeframe_series
        ),
        theses_provider=(
            lambda: tuple(
                item.to_dictionary()
                for item
                in thesis_service
                .get_report()
                .theses
            )
        ),
        outcomes_provider=(
            lambda: tuple(
                item.to_dictionary()
                for item
                in outcome_service
                .overview(
                    limit=1000
                )
                .latest
            )
        ),
        regime_service=(
            MarketRegimeService()
        ),
        timeframe_service=(
            MultiTimeframeService()
        ),
        calibration_service=(
            BayesianConfidenceService()
        ),
        explanation_service=(
            ExplainableDecisionService()
        ),
    )



def create_operation_diagnostics_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> OperationDiagnosticsService:
    service = OperationDiagnosticsService(
        repository=(
            OperationDiagnosticsRepository(
                database_path=database_path
            )
        )
    )
    service.initialize()
    return service


def create_intelligence_observability_service(
    *,
    database_path: str = (
        DEFAULT_APPLICATION_DATABASE_PATH
    ),
) -> IntelligenceObservabilityService:
    job_service = create_job_service(
        database_path=database_path
    )

    return IntelligenceObservabilityService(
        jobs_provider=(
            lambda limit: (
                job_service.list_recent(
                    limit=limit
                )
            )
        ),
        diagnostics_service=(
            create_operation_diagnostics_service(
                database_path=database_path
            )
        ),
    )
