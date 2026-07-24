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
from app.symbol_decision_service import SymbolDecisionService
from app.symbol_decision_history_service import SymbolDecisionHistoryService
from app.symbol_decision_repository import SymbolDecisionRepository
from app.decision_intelligence_service import DecisionIntelligenceService
from app.decision_trace_repository import DecisionTraceRepository
from app.copilot_change_service import CopilotChangeService
from app.copilot_history_repository import CopilotHistoryRepository

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
            create_infrastructure_status_service
        ),
        recent_jobs_provider=(
            create_recent_jobs_provider()
        ),
        schedules_provider=(
            create_schedule_provider()
        ),
        intelligence_snapshot_provider=(
            create_intelligence_snapshot
        ),
        graduation_status_provider=(
            create_graduation_snapshot
        ),
    )


def create_copilot_change_service(
    *,
    database_path: str = DEFAULT_APPLICATION_DATABASE_PATH,
) -> CopilotChangeService:
    service = CopilotChangeService(
        repository=CopilotHistoryRepository(
            database_path=database_path
        ),
        overview_provider=(
            lambda: create_copilot_service(
                database_path=database_path
            ).dashboard_overview()
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
            lambda: create_copilot_service(
                database_path=database_path
            ).dashboard_overview()
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
