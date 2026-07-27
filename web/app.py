"""
CORS-patched web/app.py for the Kairo frontend.

Changes vs original:
  1. CORSMiddleware added — reads FRONTEND_ORIGINS env var (comma-separated).
     Also accepts all *.replit.dev / *.replit.app origins and localhost by default
     via allow_origin_regex, so FRONTEND_ORIGINS is optional.
  2. Session cookie samesite/secure made configurable via
     COOKIE_SAMESITE (default: lax) and COOKIE_SECURE (default: true).
  3. Login response now also returns session_token in the JSON body.
  4. require_authenticated_user and require_csrf_user accept the session token
     from an X-Session-Token header in addition to (or instead of) the cookie.
     This lets the Kairo frontend bypass SameSite=Lax restrictions on cross-origin
     POST requests without requiring HTTPS or a tunnel in development.

Minimal .env required:
  FRONTEND_ORIGINS=https://your-kairo-domain.replit.dev   # optional with regex fallback
  COOKIE_SAMESITE=lax
  COOKIE_SECURE=true
"""

import os
from datetime import datetime
from dataclasses import asdict
from collections.abc import Callable
from typing import Annotated, Protocol

from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Response,
    Query,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import (
    AliasChoices,
    BaseModel,
    Field,
    field_validator,
    model_validator,
)

from app.application_errors import (
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DataStoreError,
    ProviderUnavailableError,
    TradingOperationError,
)
from app.authentication import AuthenticatedUser
from app.market_data import MarketDataUnavailableError
from app.job_reliability_service import JobReliabilityService
from app.job import (
    JobStatus,
    JobType,
)
from app.scheduled_task import CatchUpPolicy, ScheduleKind, ScheduledTask
from app.shadow_decision import ShadowAction
from app.paper_trading_process import (
    PaperTradingProcessStatus,
)
from app.operations_query_service import (
    OperationsQueryRequest,
)
from app.run_history import RunType
from app.system_status_service import (
    SystemStatusRequest,
)
from web.dependencies import (
    create_audit_service,
    create_authentication_service,
    create_intelligence_service,
    create_job_service,
    create_operations_query_service,
    create_paper_trading_controller,
    create_research_query_service,
    create_run_history_service,
    create_shadow_trading_service,
    create_shadow_performance_service,
    create_intelligence_graduation_service,
    create_infrastructure_status_service,
    create_daily_briefing_service,
    create_system_status_service,
    create_schedule_management_service,
    create_copilot_service,
    create_intelligence_observability_service,
    create_advanced_intelligence_service,
    create_adaptive_intelligence_service,
    create_decision_outcome_service,
    create_decision_memory_service,
    create_macro_capability_provider,
    create_technical_historical_client,
    create_technical_analysis_service,
    create_investment_thesis_service,
    create_decision_engine_service,
    create_symbol_decision_service,
    create_symbol_decision_history_service,
    create_decision_intelligence_service,
    create_copilot_change_service,
    create_performance_review_service,
    create_historical_similarity_service,
    )


# ─── CORS / cookie helpers ────────────────────────────────────────────────────

def _cors_origins() -> list[str]:
    """
    Read FRONTEND_ORIGINS from the environment.
    Accepts a comma-separated list:
        FRONTEND_ORIGINS=https://kairo.replit.app,http://localhost:5173
    """
    raw = os.environ.get("FRONTEND_ORIGINS", "").strip()
    if not raw:
        return []
    return [o.strip() for o in raw.split(",") if o.strip()]


def _cookie_samesite() -> str:
    return os.environ.get("COOKIE_SAMESITE", "lax").lower()


def _cookie_secure() -> bool:
    return os.environ.get("COOKIE_SECURE", "true").lower() in ("1", "true", "yes")


# ─── Protocol definitions (unchanged) ────────────────────────────────────────

class AuthenticationServiceLike(Protocol):
    def login(self, *, username: str, password: str):
        ...

    def authenticate(
        self,
        *,
        session_token: str | None,
    ) -> AuthenticatedUser:
        ...

    def verify_csrf(
        self,
        *,
        session_token: str | None,
        csrf_token: str | None,
    ) -> AuthenticatedUser:
        ...

    def logout(
        self,
        *,
        session_token: str | None,
    ) -> None:
        ...


class AuditServiceLike(Protocol):
    def record(self, **kwargs):
        ...

    def list_recent(
        self,
        *,
        limit: int = 100,
    ):
        ...


class ShadowTradingServiceLike(Protocol):
    def list_decisions(self, **kwargs):
        ...

    def get_summary(self):
        ...


class IntelligenceServiceLike(Protocol):
    def get_snapshot(self):
        ...


class SystemStatusServiceLike(Protocol):
    def get_status(
        self,
        *,
        request: SystemStatusRequest,
    ):
        ...


class RunHistoryServiceLike(Protocol):
    def initialize(self) -> None:
        ...

    def list_recent(
        self,
        *,
        limit: int = 50,
        run_type: RunType | None = None,
    ):
        ...


class JobServiceLike(Protocol):
    def enqueue(self, *, job_type, payload):
        ...

    def get(self, *, job_id: str):
        ...

    def list_recent(
        self,
        *,
        limit: int = 50,
        status=None,
        job_type=None,
    ):
        ...



class ScheduleManagementServiceLike(Protocol):
    def list(self): ...
    def get(self, *, schedule_id: str): ...
    def create(self, **kwargs): ...
    def update(self, *, schedule_id: str, **kwargs): ...
    def set_enabled(self, *, schedule_id: str, enabled: bool): ...
    def delete(self, *, schedule_id: str): ...
    def run_now(self, *, schedule_id: str): ...

class PaperTradingControllerLike(Protocol):
    def get_status(
        self,
    ) -> PaperTradingProcessStatus:
        ...

    def start(
        self,
    ) -> PaperTradingProcessStatus:
        ...

    def stop(
        self,
    ) -> PaperTradingProcessStatus:
        ...


class OperationsQueryServiceLike(Protocol):
    def get_portfolio(self, *, request):
        ...

    def list_positions(self, *, request):
        ...

    def list_orders(self, **kwargs):
        ...

    def get_risk_status(self, *, request):
        ...

    def get_latest_reconciliation(
        self,
        *,
        request,
    ):
        ...


class ResearchQueryServiceLike(Protocol):
    def get_latest_report(self):
        ...

    def list_signals(self, **kwargs):
        ...

    def list_outcomes(self, **kwargs):
        ...

    def get_news_summary(self):
        ...

class CopilotServiceLike(Protocol):
    def answer(
        self,
        *,
        question: str,
    ):
        ...

    def operational_overview(
        self,
    ):
        ...

    def dashboard_overview(
        self,
    ):
        ...

# ─── Request / response models (unchanged) ───────────────────────────────────

class CopilotQueryRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=500,
    )

    @field_validator("question")
    @classmethod
    def normalize_question(
        cls,
        value: str,
    ) -> str:
        cleaned = " ".join(
            value.strip().split()
        )

        if not cleaned:
            raise ValueError(
                "Copilot question is required."
            )

        return cleaned

class LoginRequest(BaseModel):
    username: str
    password: str


class NewsResearchJobRequest(BaseModel):
    market_data_provider: str = Field(
        default="TWELVE_DATA",
        validation_alias=AliasChoices(
            "market_data_provider",
            "provider",
        ),
    )
    symbols: list[str] | None = None
    watchlist_path: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "watchlist_path",
            "watchlist",
        ),
    )
    max_price_requests: int = Field(default=5, ge=0)

    @field_validator("market_data_provider")
    @classmethod
    def normalize_market_data_provider(
        cls,
        value: str,
    ) -> str:
        cleaned = value.upper().strip()
        if not cleaned:
            raise ValueError(
                "Provider is required."
            )
        return cleaned

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(
        cls,
        value: list[str] | None,
    ) -> list[str] | None:
        if value is None:
            return None
        cleaned = list(
            dict.fromkeys(
                symbol.upper().strip()
                for symbol in value
                if symbol.strip()
            )
        )
        return cleaned or None

    @model_validator(mode="after")
    def validate_target(self):
        source_count = sum(
            source is not None
            for source in (
                self.symbols,
                self.watchlist_path,
            )
        )
        if source_count != 1:
            raise ValueError(
                "Provide either symbols or a watchlist, but not both."
            )
        return self

    def to_payload(self) -> dict:
        payload: dict = {
            "market_data_provider": self.market_data_provider,
            "max_price_requests": self.max_price_requests,
        }
        if self.symbols is not None:
            payload["symbols"] = self.symbols
        if self.watchlist_path is not None:
            payload["watchlist_path"] = self.watchlist_path
        return payload


class IntelligenceCycleJobRequest(NewsResearchJobRequest):
    pass


class StrategyReportJobRequest(BaseModel):
    force: bool = False


class ShadowAnalysisJobRequest(BaseModel):
    force: bool = False



class ScheduleWriteRequest(BaseModel):
    schedule_id: str | None = None
    task_type: JobType
    enabled: bool = True
    schedule_kind: ScheduleKind
    timezone_name: str = "UTC"
    interval_seconds: int | None = Field(default=None, gt=0)
    local_hour: int | None = Field(default=None, ge=0, le=23)
    local_minute: int | None = Field(default=None, ge=0, le=59)
    weekday: int | None = Field(default=None, ge=0, le=6)
    payload: dict[str, object] = Field(default_factory=dict)
    catch_up_policy: CatchUpPolicy = CatchUpPolicy.RUN_ONCE
    catch_up_window_seconds: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.task_type not in {JobType.NEWS_RESEARCH_CYCLE, JobType.STRATEGY_REPORT, JobType.SHADOW_ANALYSIS, JobType.INTELLIGENCE_CYCLE}:
            raise ValueError("This job type cannot be scheduled.")
        if self.schedule_kind == ScheduleKind.INTERVAL and self.interval_seconds is None:
            raise ValueError("Interval schedules require interval_seconds.")
        if self.schedule_kind != ScheduleKind.INTERVAL and (self.local_hour is None or self.local_minute is None):
            raise ValueError("Calendar schedules require local_hour and local_minute.")
        if self.schedule_kind == ScheduleKind.WEEKLY and self.weekday is None:
            raise ValueError("Weekly schedules require weekday.")
        if self.catch_up_policy == CatchUpPolicy.RUN_IF_WITHIN_WINDOW and self.catch_up_window_seconds is None:
            raise ValueError("Catch-up window is required.")
        return self

    def service_values(self) -> dict[str, object]:
        return self.model_dump(exclude={"schedule_id"})

class ScheduleUpdateRequest(ScheduleWriteRequest):
    schedule_id: str | None = Field(default=None, exclude=True)

class PaperTradingStartRequest(BaseModel):
    confirm_demo_paper_trading: bool

    @model_validator(mode="after")
    def validate_confirmation(self):
        if not self.confirm_demo_paper_trading:
            raise ValueError(
                "DEMO paper-trading confirmation "
                "must be explicitly set to true."
            )
        return self


class PaperTradingStopRequest(BaseModel):
    confirm_stop: bool

    @model_validator(mode="after")
    def validate_confirmation(self):
        if not self.confirm_stop:
            raise ValueError(
                "Paper-trading stop confirmation "
                "must be explicitly set to true."
            )
        return self


# ─── Error helpers ────────────────────────────────────────────────────────────

def _application_error_status_code(
    error: ApplicationError,
) -> int:
    if isinstance(error, AuthenticationError):
        return 401
    if isinstance(error, AuthorizationError):
        return 403
    if isinstance(error, TradingOperationError):
        return 409
    if isinstance(error, ProviderUnavailableError):
        return 503
    if isinstance(
        error,
        (
            ConfigurationError,
            DataStoreError,
        ),
    ):
        return 500
    return 400


# ─── App factory ─────────────────────────────────────────────────────────────

def create_app(
    *,
    infrastructure_status_service_factory: (
        Callable[[], object] | None
    ) = None,
    daily_briefing_service_factory: (
        Callable[[], object] | None
    ) = None,
    authentication_service_factory: (
        Callable[[], AuthenticationServiceLike]
        | None
    ) = None,
    audit_service_factory: (
        Callable[[], AuditServiceLike]
        | None
    ) = None,
    shadow_performance_service_factory: (
        Callable[[], object] | None
    ) = None,
    intelligence_graduation_service_factory: (
        Callable[[], object] | None
    ) = None,
    shadow_trading_service_factory: (
        Callable[[], ShadowTradingServiceLike]
        | None
    ) = None,
    intelligence_service_factory: (
        Callable[[], IntelligenceServiceLike]
        | None
    ) = None,
    system_status_service_factory: (
        Callable[[], SystemStatusServiceLike]
        | None
    ) = None,
    run_history_service_factory: (
        Callable[[], RunHistoryServiceLike]
        | None
    ) = None,
    job_service_factory: (
        Callable[[], JobServiceLike]
        | None
    ) = None,
    research_query_service_factory: (
        Callable[[], ResearchQueryServiceLike]
        | None
    ) = None,
    operations_query_service_factory: (
        Callable[[], OperationsQueryServiceLike]
        | None
    ) = None,
    schedule_management_service_factory: (
        Callable[[], ScheduleManagementServiceLike] | None
    ) = None,
    copilot_service_factory: (
        Callable[[], CopilotServiceLike]
        | None
    ) = None,   
    paper_trading_controller_factory: (
        Callable[[], PaperTradingControllerLike]
        | None
    ) = None,
    performance_review_service_factory: (
        Callable[[], object] | None
    ) = None,
    historical_similarity_service_factory: (
        Callable[[], object] | None
    ) = None,
) -> FastAPI:
    infrastructure_factory = (
        infrastructure_status_service_factory
        or create_infrastructure_status_service
    )
    daily_briefing_factory = (
        daily_briefing_service_factory
        or create_daily_briefing_service
    )
    auth_factory = (
        authentication_service_factory
        or create_authentication_service
    )
    audit_factory = (
        audit_service_factory
        or create_audit_service
    )
    shadow_performance_factory = (
        shadow_performance_service_factory
        or create_shadow_performance_service
    )
    graduation_factory = (
        intelligence_graduation_service_factory
        or create_intelligence_graduation_service
    )
    shadow_factory = (
        shadow_trading_service_factory
        or create_shadow_trading_service
    )
    intelligence_factory = (
        intelligence_service_factory
        or create_intelligence_service
    )
    status_factory = (
        system_status_service_factory
        or create_system_status_service
    )
    history_factory = (
        run_history_service_factory
        or create_run_history_service
    )
    jobs_factory = (
        job_service_factory
        or create_job_service
    )
    research_factory = (
        research_query_service_factory
        or create_research_query_service
    )
    operations_factory = (
        operations_query_service_factory
        or create_operations_query_service
    )
    schedules_factory = (
        schedule_management_service_factory
        or create_schedule_management_service
    )
    copilot_factory = (
        copilot_service_factory
        or create_copilot_service
    )
    paper_trading_factory = (
        paper_trading_controller_factory
        or create_paper_trading_controller
    )
    performance_review_factory = (
        performance_review_service_factory
        or create_performance_review_service
    )
    historical_similarity_factory = (
        historical_similarity_service_factory
        or create_historical_similarity_service
    )

    app = FastAPI(
        title="Trading Bot Platform",
        version="0.11.0",
        docs_url="/docs",
        redoc_url=None,
    )

    # ── CORS middleware ────────────────────────────────────────────────────────
    # Must be added BEFORE any route definitions.
    # allow_origins handles any explicit origins from FRONTEND_ORIGINS.
    # Only local development origins are accepted by regex. Hosted origins,
    # including Replit deployments, must be explicitly listed in
    # FRONTEND_ORIGINS when credentials are enabled.
    origins = _cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=(
            r"http://localhost(:\d+)?"
            r"|http://127\.0\.0\.1(:\d+)?"
        ),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token", "X-Session-Token"],
        expose_headers=["Set-Cookie"],
    )
    # ──────────────────────────────────────────────────────────────────────────

    def require_authenticated_user(
        trading_session: Annotated[
            str | None,
            Cookie(),
        ] = None,
        x_session_token: Annotated[
            str | None,
            Header(alias="X-Session-Token"),
        ] = None,
    ) -> AuthenticatedUser:
        # Cookie takes precedence; header is the fallback for cross-origin
        # clients that cannot rely on SameSite=Lax cookie delivery on POSTs.
        return auth_factory().authenticate(
            session_token=trading_session or x_session_token
        )

    def require_csrf_user(
        trading_session: Annotated[
            str | None,
            Cookie(),
        ] = None,
        x_session_token: Annotated[
            str | None,
            Header(alias="X-Session-Token"),
        ] = None,
        x_csrf_token: Annotated[
            str | None,
            Header(alias="X-CSRF-Token"),
        ] = None,
    ) -> AuthenticatedUser:
        return auth_factory().verify_csrf(
            session_token=trading_session or x_session_token,
            csrf_token=x_csrf_token,
        )

    def source_ip(request: Request) -> str | None:
        return (
            None
            if request.client is None
            else request.client.host
        )

    @app.exception_handler(ApplicationError)
    async def handle_application_error(
        request: Request,
        error: ApplicationError,
    ) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=(
                _application_error_status_code(error)
            ),
            content={
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "retryable": error.retryable,
                }
            },
        )

    @app.exception_handler(MarketDataUnavailableError)
    async def handle_market_data_unavailable(
        request: Request,
        error: MarketDataUnavailableError,
    ) -> JSONResponse:
        del request
        headers = {}
        if error.retry_after_seconds is not None:
            headers["Retry-After"] = str(
                max(1, int(error.retry_after_seconds))
            )
        return JSONResponse(
            status_code=503,
            content=error.to_dictionary(),
            headers=headers,
        )

    @app.post(
        "/api/auth/login",
        tags=["authentication"],
    )
    def login(
        request: LoginRequest,
        response: Response,
        http_request: Request,
    ) -> dict[str, object]:
        session = auth_factory().login(
            username=request.username,
            password=request.password,
        )

        response.set_cookie(
            key="trading_session",
            value=session.session_token,
            httponly=True,
            secure=_cookie_secure(),
            samesite=_cookie_samesite(),
            max_age=8 * 60 * 60,
            path="/",
        )

        audit_factory().record(
            action="AUTH_LOGIN",
            outcome="SUCCEEDED",
            username=session.user.username,
            source_ip=source_ip(http_request),
        )

        return {
            "user": session.user.to_dictionary(),
            "csrf_token": session.csrf_token,
            "session_token": session.session_token,
            "expires_at": (
                session.expires_at.isoformat()
            ),
        }

    @app.post(
        "/api/auth/logout",
        tags=["authentication"],
    )
    def logout(
        response: Response,
        http_request: Request,
        user: Annotated[
            AuthenticatedUser,
            Depends(require_csrf_user),
        ],
        trading_session: Annotated[
            str | None,
            Cookie(),
        ] = None,
    ) -> dict[str, str]:
        auth_factory().logout(
            session_token=trading_session
        )
        response.delete_cookie(
            "trading_session",
            path="/",
        )
        audit_factory().record(
            action="AUTH_LOGOUT",
            outcome="SUCCEEDED",
            username=user.username,
            source_ip=source_ip(http_request),
        )
        return {"status": "logged_out"}

    @app.get(
        "/api/auth/me",
        tags=["authentication"],
    )
    def current_user(
        user: Annotated[
            AuthenticatedUser,
            Depends(require_authenticated_user),
        ],
    ) -> dict[str, str]:
        return user.to_dictionary()

    @app.get(
        "/api/audit",
        tags=["audit"],
    )
    def audit_events(
        limit: int = Query(
            default=50,
            ge=1,
            le=200,
        ),
        user: Annotated[
            AuthenticatedUser,
            Depends(require_authenticated_user),
        ] = None,
    ) -> dict[str, object]:
        del user
        events = audit_factory().list_recent(
            limit=limit
        )
        return {
            "count": len(events),
            "items": list(events),
        }

    @app.get("/health/live", tags=["health"])
    def health_live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    def health_ready() -> dict[str, str]:
        history_service = history_factory()
        history_service.initialize()
        jobs_factory()
        status_factory().get_status(
            request=SystemStatusRequest()
        )
        return {"status": "ready"}

    @app.get(
        "/api/intelligence/briefing",
        tags=["intelligence"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def intelligence_briefing(
    ) -> dict[str, object]:
        return (
            daily_briefing_factory()
            .get_briefing()
            .to_dictionary()
        )

    @app.get(
        "/api/intelligence/snapshot",
        tags=["intelligence"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def intelligence_snapshot(
    ) -> dict[str, object]:
        return (
            intelligence_factory()
            .get_snapshot()
            .to_dictionary()
        )

    @app.post(
        "/api/jobs/shadow-analysis",
        status_code=202,
        tags=["intelligence"],
    )
    def queue_shadow_analysis(
        request: ShadowAnalysisJobRequest,
        http_request: Request,
        user: Annotated[
            AuthenticatedUser,
            Depends(require_csrf_user),
        ],
    ) -> dict[str, object]:
        job = jobs_factory().enqueue(
            job_type=JobType.SHADOW_ANALYSIS,
            payload={"force": request.force},
        )
        audit_factory().record(
            action="SHADOW_ANALYSIS_JOB_QUEUED",
            outcome="SUCCEEDED",
            username=user.username,
            source_ip=source_ip(http_request),
            target_id=job.job_id,
            metadata={"force": request.force},
        )
        return job.to_dictionary()

    @app.get(
        "/api/shadow-performance",
        tags=["intelligence"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def shadow_performance(
    ) -> dict[str, object]:
        return (
            shadow_performance_factory()
            .get_report()
            .to_dictionary()
        )

    @app.get(
        "/api/intelligence/graduation-status",
        tags=["intelligence"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def intelligence_graduation_status(
    ) -> dict[str, object]:
        return (
            graduation_factory()
            .get_status()
            .to_dictionary()
        )

    @app.get(
        "/api/shadow-decisions",
        tags=["intelligence"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def shadow_decisions(
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        symbol: str | None = None,
        action: ShadowAction | None = None,
    ) -> dict[str, object]:
        return shadow_factory().list_decisions(
            limit=limit,
            offset=offset,
            symbol=symbol,
            action=action,
        )

    @app.get(
        "/api/shadow-decisions/summary",
        tags=["intelligence"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def shadow_decision_summary(
    ) -> dict[str, object]:
        return shadow_factory().get_summary()

    @app.get(
        "/api/infrastructure/status",
        tags=["system"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def infrastructure_status(
    ) -> dict[str, object]:
        return (
            infrastructure_factory()
            .get_status()
            .to_dictionary()
        )

    @app.get(
        "/api/market-data/health",
        tags=["system"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def market_data_health(
    ) -> dict[str, object]:
        return (
            create_technical_historical_client()
            .health_snapshot()
        )

    @app.get(
        "/api/workers/job/status",
        tags=["system"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def job_worker_status(
    ) -> dict[str, object]:
        return (
            infrastructure_factory()
            .get_worker_status()
            .to_dictionary()
        )


    @app.get(
        "/api/workers/job/reliability",
        tags=["system"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def job_worker_reliability(
    ) -> dict[str, object]:
        return JobReliabilityService().get_status()

    @app.get(
        "/api/copilot/history",
        tags=["copilot"],
    )
    def copilot_history(
        user: Annotated[
            AuthenticatedUser,
            Depends(require_authenticated_user),
        ],
        limit: int = Query(default=100, ge=1, le=500),
    ) -> dict[str, object]:
        del user
        items = create_copilot_change_service().list_history(
            limit=limit
        )
        return {
            "items": [
                item.to_dictionary()
                for item in items
            ]
        }

    @app.get(
        "/api/copilot/change-summary",
        tags=["copilot"],
    )
    def copilot_change_summary(
        user: Annotated[
            AuthenticatedUser,
            Depends(require_authenticated_user),
        ],
    ) -> dict[str, object]:
        del user
        return (
            create_copilot_change_service()
            .change_summary()
            .to_dictionary()
        )


    @app.get(
        "/api/copilot/decision-trace/latest",
        tags=["copilot"],
    )
    def latest_decision_trace(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        return (
            create_decision_intelligence_service()
            .latest()
            .to_dictionary()
        )

    @app.get(
        "/api/copilot/decision-traces",
        tags=["copilot"],
    )
    def list_decision_traces(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
        limit: int = Query(
            default=50,
            ge=1,
            le=250,
        ),
    ) -> dict[str, object]:
        del user

        items = (
            create_decision_intelligence_service()
            .list_recent(
                limit=limit
            )
        )

        return {
            "items": [
                item.to_dictionary()
                for item in items
            ]
        }


    @app.get(
        "/api/copilot/symbol-decisions",
        tags=["copilot"],
    )
    def list_symbol_decisions(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        items = (
            create_symbol_decision_service()
            .list_current()
        )

        return {
            "items": [
                item.to_dictionary()
                for item in items
            ]
        }

    @app.get(
        "/api/copilot/symbol-decisions/{symbol}/history",
        tags=["copilot"],
    )
    def get_symbol_decision_history(
        symbol: str,
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
        limit: int = Query(
            default=100,
            ge=1,
            le=500,
        ),
    ) -> dict[str, object]:
        del user

        items = (
            create_symbol_decision_history_service()
            .list_history(
                symbol=symbol,
                limit=limit,
            )
        )

        return {
            "symbol": symbol.upper(),
            "items": [
                item.to_dictionary()
                for item in items
            ],
        }

    @app.get(
        "/api/copilot/symbol-decisions/{symbol}/change-summary",
        tags=["copilot"],
    )
    def get_symbol_decision_change_summary(
        symbol: str,
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        summary = (
            create_symbol_decision_history_service()
            .compare_latest(
                symbol=symbol
            )
        )

        if summary is None:
            return {
                "available": False,
                "symbol": symbol.upper(),
                "summary": None,
            }

        return {
            "available": True,
            "symbol": summary.symbol,
            "summary": (
                summary.to_dictionary()
            ),
        }


    @app.get(
        "/api/copilot/symbol-decisions/{symbol}",
        tags=["copilot"],
    )
    def get_symbol_decision(
        symbol: str,
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        trace = (
            create_symbol_decision_service()
            .get_current(
                symbol=symbol
            )
        )

        if trace is None:
            return {
                "available": False,
                "symbol": symbol.upper(),
                "trace": None,
            }

        return {
            "available": True,
            "symbol": trace.symbol,
            "trace": trace.to_dictionary(),
        }


    @app.get(
        "/api/copilot/investment-decisions",
        tags=["copilot"],
    )
    def investment_decisions(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        return (
            create_decision_engine_service()
            .get_report()
            .to_dictionary()
        )


    @app.get(
        "/api/copilot/historical-similarity/{symbol}",
        tags=["copilot"],
    )
    def historical_similarity(
        symbol: str,
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
        minimum_similarity_percent: float = Query(
            default=65.0,
            ge=0.0,
            le=100.0,
        ),
        limit: int = Query(
            default=12,
            ge=1,
            le=50,
        ),
    ) -> dict[str, object]:
        del user

        try:
            return (
                historical_similarity_factory()
                .analyse(
                    symbol=symbol,
                    minimum_similarity_percent=(
                        minimum_similarity_percent
                    ),
                    limit=limit,
                )
                .to_dictionary()
            )
        except LookupError as error:
            raise HTTPException(
                status_code=404,
                detail=str(error),
            ) from error


    @app.get(
        "/api/copilot/investment-theses",
        tags=["copilot"],
    )
    def investment_theses(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        report = (
            create_investment_thesis_service()
            .get_report()
        )

        create_decision_memory_service(
        ).capture_report(
            report=report
        )

        return report.to_dictionary()


    @app.get(
        "/api/copilot/technical-analysis/{symbol}",
        tags=["copilot"],
    )
    def technical_analysis(
        symbol: str,
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        market_data = (
            create_technical_historical_client()
            .get_daily_bars_result(
                symbol=symbol,
                output_size=260,
            )
        )

        payload = (
            create_technical_analysis_service()
            .analyse(
                symbol=symbol,
                bars=list(market_data.bars),
            )
            .to_dictionary()
        )
        payload["market_data"] = market_data.to_metadata()
        return payload


    @app.get(
        "/api/copilot/macro-analysis",
        tags=["copilot"],
    )
    def macro_analysis(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        payload = (
            create_macro_capability_provider()
            .get_analysis()
            .to_dictionary()
        )
        payload["market_data_health"] = (
            create_technical_historical_client()
            .health_snapshot()
        )
        return payload


    @app.get(
        "/api/copilot/decision-memory",
        tags=["copilot"],
    )
    def decision_memory(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
        limit: int = Query(
            default=10,
            ge=1,
            le=100,
        ),
    ) -> dict[str, object]:
        del user

        return (
            create_decision_memory_service()
            .overview(
                limit=limit
            )
            .to_dictionary()
        )


    @app.get(
        "/api/copilot/decision-outcomes",
        tags=["copilot"],
    )
    def decision_outcomes(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
        limit: int = Query(
            default=20,
            ge=1,
            le=100,
        ),
    ) -> dict[str, object]:
        del user

        return (
            create_decision_outcome_service()
            .overview(
                limit=limit
            )
            .to_dictionary()
        )


    @app.post(
        "/api/copilot/decision-outcomes/capture",
        tags=["copilot"],
    )
    def capture_decision_outcomes(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        return (
            create_decision_outcome_service()
            .capture_due()
            .to_dictionary()
        )


    @app.get(
        "/api/copilot/adaptive-intelligence",
        tags=["copilot"],
    )
    def adaptive_intelligence(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        return (
            create_adaptive_intelligence_service()
            .report()
            .to_dictionary()
        )


    @app.post(
        "/api/copilot/strategy-evolution/propose",
        tags=["copilot"],
    )
    def propose_strategy_evolution(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        proposals = (
            create_adaptive_intelligence_service()
            .propose_evolution()
        )

        return {
            "created_count": len(
                proposals
            ),
            "proposals": [
                item.to_dictionary()
                for item in proposals
            ],
        }


    @app.get(
        "/api/copilot/advanced-intelligence",
        tags=["copilot"],
    )
    def advanced_intelligence(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        payload = (
            create_advanced_intelligence_service()
            .report()
            .to_dictionary()
        )
        payload["market_data_health"] = (
            create_technical_historical_client()
            .health_snapshot()
        )
        return payload


    @app.get(
        "/api/copilot/intelligence-health",
        tags=["copilot"],
    )
    def intelligence_health(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
        limit: int = Query(
            default=20,
            ge=1,
            le=100,
        ),
    ) -> dict[str, object]:
        del user

        return (
            create_intelligence_observability_service()
            .overview(
                limit=limit
            )
            .to_dictionary()
        )


    @app.get(
        "/api/jobs/{job_id}/diagnostics",
        tags=["jobs"],
    )
    def job_diagnostics(
        job_id: str,
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        return (
            create_intelligence_observability_service()
            .job_report(
                job_id=job_id
            )
            .to_dictionary()
        )


    @app.get(
        "/api/copilot/overview",
        tags=["copilot"],
    )
    def copilot_overview(
        user: Annotated[
            AuthenticatedUser,
            Depends(
                require_authenticated_user
            ),
        ],
    ) -> dict[str, object]:
        del user

        return (
            copilot_factory()
            .dashboard_overview()
            .to_dictionary()
        )


    @app.get(
        "/api/copilot/suggestions",
        tags=["copilot"],
    )
    def copilot_suggestions(
        user: Annotated[
            AuthenticatedUser,
            Depends(require_authenticated_user),
        ],
    ) -> dict[str, object]:
        del user

        return {
            "items": [
                "Is KAIRO healthy?",
                "What failed recently?",
                "What is running now?",
                "What happens next?",
                "Give me an operational overview.",
            ]
        }

    @app.post(
        "/api/copilot/query",
        tags=["copilot"],
    )
    def copilot_query(
        request: CopilotQueryRequest,
        user: Annotated[
            AuthenticatedUser,
            Depends(require_authenticated_user),
        ],
    ) -> dict[str, object]:
        del user

        response = copilot_factory().answer(
            question=request.question
        )

        return asdict(response)

    @app.get(
        "/api/status",
        dependencies=[Depends(require_authenticated_user)],
    )
    def system_status() -> dict[str, object]:
        result = status_factory().get_status(
            request=SystemStatusRequest()
        )
        return result.to_dictionary()

    @app.get(
        "/api/run-history",
        tags=["operations"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def run_history(
        limit: int = Query(
            default=20,
            ge=1,
            le=200,
        ),
        run_type: RunType | None = None,
    ) -> dict[str, object]:
        service = history_factory()
        service.initialize()
        records = service.list_recent(
            limit=limit,
            run_type=run_type,
        )
        return {
            "count": len(records),
            "items": [
                record.to_dictionary()
                for record in records
            ],
        }

    @app.post(
        "/api/jobs/news-research",
        status_code=202,
        tags=["jobs"],
    )
    def queue_news_research(
        request: NewsResearchJobRequest,
        http_request: Request,
        user: Annotated[
            AuthenticatedUser,
            Depends(require_csrf_user),
        ],
    ) -> dict[str, object]:
        job = jobs_factory().enqueue(
            job_type=JobType.NEWS_RESEARCH_CYCLE,
            payload=request.to_payload(),
        )
        audit_factory().record(
            action="NEWS_RESEARCH_JOB_QUEUED",
            outcome="SUCCEEDED",
            username=user.username,
            source_ip=source_ip(http_request),
            target_id=job.job_id,
            metadata={
                "market_data_provider": request.market_data_provider,
            },
        )
        return job.to_dictionary()

    @app.post(
        "/api/jobs/intelligence-cycle",
        status_code=202,
        tags=["jobs"],
    )
    def queue_intelligence_cycle(
        request: IntelligenceCycleJobRequest,
        http_request: Request,
        user: Annotated[
            AuthenticatedUser,
            Depends(require_csrf_user),
        ],
    ) -> dict[str, object]:
        job = jobs_factory().enqueue(
            job_type=JobType.INTELLIGENCE_CYCLE,
            payload=request.to_payload(),
        )
        audit_factory().record(
            action="INTELLIGENCE_CYCLE_JOB_QUEUED",
            outcome="SUCCEEDED",
            username=user.username,
            source_ip=source_ip(http_request),
            target_id=job.job_id,
            metadata={
                "market_data_provider": request.market_data_provider,
            },
        )
        return job.to_dictionary()

    @app.post(
        "/api/jobs/strategy-report",
        status_code=202,
        tags=["jobs"],
    )
    def queue_strategy_report(
        request: StrategyReportJobRequest,
        http_request: Request,
        user: Annotated[
            AuthenticatedUser,
            Depends(require_csrf_user),
        ],
    ) -> dict[str, object]:
        job = jobs_factory().enqueue(
            job_type=JobType.STRATEGY_REPORT,
            payload={"force": request.force},
        )
        audit_factory().record(
            action="STRATEGY_REPORT_JOB_QUEUED",
            outcome="SUCCEEDED",
            username=user.username,
            source_ip=source_ip(http_request),
            target_id=job.job_id,
            metadata={"force": request.force},
        )
        return job.to_dictionary()

    @app.get(
        "/api/jobs",
        dependencies=[Depends(require_authenticated_user)],
    )
    def list_jobs(
        limit: int = Query(
            default=20,
            ge=1,
            le=200,
        ),
        status: JobStatus | None = None,
        job_type: JobType | None = None,
    ) -> dict[str, object]:
        records = jobs_factory().list_recent(
            limit=limit,
            status=status,
            job_type=job_type,
        )
        return {
            "count": len(records),
            "items": [
                record.to_dictionary()
                for record in records
            ],
        }

    @app.get(
        "/api/jobs/{job_id}",
        dependencies=[Depends(require_authenticated_user)],
    )
    def get_job(job_id: str) -> dict[str, object]:
        record = jobs_factory().get(job_id=job_id)

        if record is None:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "code": "JOB_NOT_FOUND",
                        "message": "Job was not found.",
                        "retryable": False,
                    }
                },
            )

        return record.to_dictionary()


    def schedule_dictionary(task: ScheduledTask) -> dict[str, object]:
        return {
            "schedule_id": task.schedule_id, "task_type": task.task_type.value,
            "enabled": task.enabled, "schedule_kind": task.schedule_kind.value,
            "timezone_name": task.timezone_name, "interval_seconds": task.interval_seconds,
            "local_hour": task.local_hour, "local_minute": task.local_minute,
            "weekday": task.weekday, "next_run_at": task.next_run_at.isoformat(),
            "last_run_at": None if task.last_run_at is None else task.last_run_at.isoformat(),
            "last_job_id": task.last_job_id, "last_status": task.last_status,
            "payload": dict(task.payload), "catch_up_policy": task.catch_up_policy.value,
            "catch_up_window_seconds": task.catch_up_window_seconds,
            "created_at": None if task.created_at is None else task.created_at.isoformat(),
            "updated_at": None if task.updated_at is None else task.updated_at.isoformat(),
        }

    @app.get("/api/schedules", tags=["schedules"])
    def list_schedules(user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)]) -> dict[str, object]:
        del user
        items = schedules_factory().list()
        return {"count": len(items), "items": [schedule_dictionary(item) for item in items]}

    @app.get("/api/schedules/{schedule_id}", tags=["schedules"])
    def get_schedule(schedule_id: str, user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)]):
        del user
        item = schedules_factory().get(schedule_id=schedule_id)
        if item is None:
            return JSONResponse(status_code=404, content={"error": {"code": "SCHEDULE_NOT_FOUND", "message": "Schedule was not found.", "retryable": False}})
        return schedule_dictionary(item)

    @app.post("/api/schedules", status_code=201, tags=["schedules"])
    def create_schedule(request: ScheduleWriteRequest, http_request: Request, user: Annotated[AuthenticatedUser, Depends(require_csrf_user)]):
        item = schedules_factory().create(schedule_id=request.schedule_id, **request.service_values())
        audit_factory().record(action="SCHEDULE_CREATED", outcome="SUCCEEDED", username=user.username, source_ip=source_ip(http_request), target_id=item.schedule_id, metadata={"task_type": item.task_type.value})
        return schedule_dictionary(item)

    @app.put("/api/schedules/{schedule_id}", tags=["schedules"])
    def update_schedule(schedule_id: str, request: ScheduleUpdateRequest, http_request: Request, user: Annotated[AuthenticatedUser, Depends(require_csrf_user)]):
        item = schedules_factory().update(schedule_id=schedule_id, **request.service_values())
        if item is None:
            return JSONResponse(status_code=404, content={"error": {"code": "SCHEDULE_NOT_FOUND", "message": "Schedule was not found.", "retryable": False}})
        audit_factory().record(action="SCHEDULE_UPDATED", outcome="SUCCEEDED", username=user.username, source_ip=source_ip(http_request), target_id=schedule_id)
        return schedule_dictionary(item)

    def change_schedule_state(schedule_id: str, enabled: bool, http_request: Request, user: AuthenticatedUser):
        item = schedules_factory().set_enabled(schedule_id=schedule_id, enabled=enabled)
        if item is None:
            return JSONResponse(status_code=404, content={"error": {"code": "SCHEDULE_NOT_FOUND", "message": "Schedule was not found.", "retryable": False}})
        audit_factory().record(action="SCHEDULE_ENABLED" if enabled else "SCHEDULE_DISABLED", outcome="SUCCEEDED", username=user.username, source_ip=source_ip(http_request), target_id=schedule_id)
        return schedule_dictionary(item)

    @app.post("/api/schedules/{schedule_id}/enable", tags=["schedules"])
    def enable_schedule(schedule_id: str, http_request: Request, user: Annotated[AuthenticatedUser, Depends(require_csrf_user)]):
        return change_schedule_state(schedule_id, True, http_request, user)

    @app.post("/api/schedules/{schedule_id}/disable", tags=["schedules"])
    def disable_schedule(schedule_id: str, http_request: Request, user: Annotated[AuthenticatedUser, Depends(require_csrf_user)]):
        return change_schedule_state(schedule_id, False, http_request, user)

    @app.post("/api/schedules/{schedule_id}/run-now", status_code=202, tags=["schedules"])
    def run_schedule_now(schedule_id: str, http_request: Request, user: Annotated[AuthenticatedUser, Depends(require_csrf_user)]):
        job = schedules_factory().run_now(schedule_id=schedule_id)
        if job is None:
            return JSONResponse(status_code=404, content={"error": {"code": "SCHEDULE_NOT_FOUND", "message": "Schedule was not found.", "retryable": False}})
        audit_factory().record(action="SCHEDULE_RUN_NOW_QUEUED", outcome="SUCCEEDED", username=user.username, source_ip=source_ip(http_request), target_id=schedule_id, metadata={"job_id": job.job_id})
        return job.to_dictionary()

    @app.delete("/api/schedules/{schedule_id}", status_code=204, tags=["schedules"])
    def delete_schedule(schedule_id: str, http_request: Request, user: Annotated[AuthenticatedUser, Depends(require_csrf_user)]):
        if not schedules_factory().delete(schedule_id=schedule_id):
            return JSONResponse(status_code=404, content={"error": {"code": "SCHEDULE_NOT_FOUND", "message": "Schedule was not found.", "retryable": False}})
        audit_factory().record(action="SCHEDULE_DELETED", outcome="SUCCEEDED", username=user.username, source_ip=source_ip(http_request), target_id=schedule_id)
        return Response(status_code=204)

    @app.get("/api/scheduler/status", tags=["schedules"])
    def scheduler_status(user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)]):
        del user
        return infrastructure_factory().get_scheduler_status().to_dictionary()

    @app.get(
        "/api/research/latest",
        tags=["research"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def latest_research_report() -> dict[str, object]:
        report = research_factory().get_latest_report()
        return {
            "available": report is not None,
            "report": report,
        }

    @app.get(
        "/api/news/signals",
        tags=["research"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def news_signals(
        symbol: str | None = None,
        sentiment: str | None = None,
        event_type: str | None = None,
        is_material: bool | None = None,
        minimum_confidence: float | None = Query(
            default=None,
            ge=0.0,
            le=1.0,
        ),
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=200),
    ) -> dict[str, object]:
        result = research_factory().list_signals(
            symbol=symbol,
            sentiment=sentiment,
            event_type=event_type,
            is_material=is_material,
            minimum_confidence=minimum_confidence,
            offset=offset,
            limit=limit,
        )
        return result.to_dictionary()

    @app.get(
        "/api/news/outcomes",
        tags=["research"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def news_outcomes(
        symbol: str | None = None,
        horizon: str | None = None,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=200),
    ) -> dict[str, object]:
        result = research_factory().list_outcomes(
            symbol=symbol,
            horizon=horizon,
            offset=offset,
            limit=limit,
        )
        return result.to_dictionary()

    @app.get(
        "/api/news/summary",
        tags=["research"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def news_summary() -> dict[str, object]:
        return research_factory().get_news_summary()

    @app.get(
        "/api/paper-trading/status",
        tags=["paper-trading"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def paper_trading_status(
    ) -> dict[str, object]:
        return (
            paper_trading_factory()
            .get_status()
            .to_dictionary()
        )

    @app.post(
        "/api/paper-trading/start",
        status_code=202,
        tags=["paper-trading"],
    )
    def start_paper_trading(
        request: PaperTradingStartRequest,
        http_request: Request,
        user: Annotated[
            AuthenticatedUser,
            Depends(require_csrf_user),
        ],
    ) -> dict[str, object]:
        del request

        result = (
            paper_trading_factory()
            .start()
        )
        audit_factory().record(
            action="PAPER_TRADING_STARTED",
            outcome="SUCCEEDED",
            username=user.username,
            source_ip=source_ip(http_request),
            target_id=(
                None
                if result.process_id is None
                else str(result.process_id)
            ),
        )
        return result.to_dictionary()

    @app.post(
        "/api/paper-trading/stop",
        status_code=202,
        tags=["paper-trading"],
    )
    def stop_paper_trading(
        request: PaperTradingStopRequest,
        http_request: Request,
        user: Annotated[
            AuthenticatedUser,
            Depends(require_csrf_user),
        ],
    ) -> dict[str, object]:
        del request

        result = (
            paper_trading_factory()
            .stop()
        )
        audit_factory().record(
            action="PAPER_TRADING_STOP_REQUESTED",
            outcome="SUCCEEDED",
            username=user.username,
            source_ip=source_ip(http_request),
            target_id=(
                None
                if result.process_id is None
                else str(result.process_id)
            ),
        )
        return result.to_dictionary()


    @app.get(
        "/api/performance/review",
        tags=["performance"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def performance_review(
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> dict[str, object]:
        return performance_review_factory().generate(
            start=start,
            end=end,
        )

    @app.get(
        "/api/portfolio",
        tags=["operations"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def portfolio() -> dict[str, object]:
        return operations_factory().get_portfolio(
            request=OperationsQueryRequest()
        ).to_dictionary()

    @app.get(
        "/api/positions",
        tags=["operations"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def positions() -> dict[str, object]:
        items = operations_factory().list_positions(
            request=OperationsQueryRequest()
        )
        return {
            "count": len(items),
            "items": [
                item.to_dictionary()
                for item in items
            ],
        }

    @app.get(
        "/api/orders",
        tags=["operations"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def orders(
        symbol: str | None = None,
        event: str | None = None,
        active_only: bool = False,
        unresolved_only: bool = False,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=200),
    ) -> dict[str, object]:
        return operations_factory().list_orders(
            request=OperationsQueryRequest(),
            symbol=symbol,
            event=event,
            active_only=active_only,
            unresolved_only=unresolved_only,
            offset=offset,
            limit=limit,
        ).to_dictionary()

    @app.get(
        "/api/orders/unresolved",
        tags=["operations"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def unresolved_orders(
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=200),
    ) -> dict[str, object]:
        return operations_factory().list_orders(
            request=OperationsQueryRequest(),
            unresolved_only=True,
            offset=offset,
            limit=limit,
        ).to_dictionary()

    @app.get(
        "/api/risk/status",
        tags=["operations"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def risk_status() -> dict[str, object]:
        return operations_factory().get_risk_status(
            request=OperationsQueryRequest()
        ).to_dictionary()

    @app.get(
        "/api/reconciliation/latest",
        tags=["operations"],
        dependencies=[Depends(require_authenticated_user)],
    )
    def latest_reconciliation() -> dict[str, object]:
        return (
            operations_factory()
            .get_latest_reconciliation(
                request=OperationsQueryRequest()
            )
            .to_dictionary()
        )

    return app


app = create_app()