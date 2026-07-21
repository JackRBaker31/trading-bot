"""
CORS-patched web/app.py for the Kairo frontend.

Changes vs original:
  1. CORSMiddleware added — reads FRONTEND_ORIGINS env var (comma-separated).
     Also accepts all *.replit.dev / *.replit.app origins and localhost by default
     via allow_origin_regex, so FRONTEND_ORIGINS is optional.
  2. Session cookie samesite/secure made configurable via
     COOKIE_SAMESITE (default: lax) and COOKIE_SECURE (default: false).
  3. Login response now also returns session_token in the JSON body.
  4. require_authenticated_user and require_csrf_user accept the session token
     from an X-Session-Token header in addition to (or instead of) the cookie.
     This lets the Kairo frontend bypass SameSite=Lax restrictions on cross-origin
     POST requests without requiring HTTPS or a tunnel in development.

Minimal .env required:
  FRONTEND_ORIGINS=https://your-kairo-domain.replit.dev   # optional with regex fallback
  COOKIE_SAMESITE=lax
  COOKIE_SECURE=false
"""

import os
from collections.abc import Callable
from typing import Annotated, Protocol

from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    Header,
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
from app.job import (
    JobStatus,
    JobType,
)
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
    return os.environ.get("COOKIE_SECURE", "false").lower() in ("1", "true", "yes")


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


# ─── Request / response models (unchanged) ───────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class NewsResearchJobRequest(BaseModel):
    provider: str = "TWELVE_DATA"
    symbols: list[str] | None = None
    watchlist_path: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "watchlist_path",
            "watchlist",
        ),
    )
    max_price_requests: int = Field(default=5, ge=0)

    @field_validator("provider")
    @classmethod
    def normalize_provider(
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
            "provider": self.provider,
            "max_price_requests": self.max_price_requests,
        }
        if self.symbols is not None:
            payload["symbols"] = self.symbols
        if self.watchlist_path is not None:
            payload["watchlist_path"] = self.watchlist_path
        return payload


class StrategyReportJobRequest(BaseModel):
    force: bool = False


class ShadowAnalysisJobRequest(BaseModel):
    force: bool = False


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
    paper_trading_controller_factory: (
        Callable[[], PaperTradingControllerLike]
        | None
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
    paper_trading_factory = (
        paper_trading_controller_factory
        or create_paper_trading_controller
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
    # allow_origin_regex is the fallback: covers all *.replit.dev subdomains
    # and any localhost / 127.0.0.1 port — so it works out of the box without
    # needing FRONTEND_ORIGINS set in .env.
    origins = _cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=(
            r"https://.*\.replit\.dev"
            r"|https://.*\.replit\.app"
            r"|http://localhost(:\d+)?"
            r"|http://127\.0\.0\.1(:\d+)?"
        ),
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
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
    )
    def shadow_decision_summary(
    ) -> dict[str, object]:
        return shadow_factory().get_summary()

    @app.get(
        "/api/infrastructure/status",
        tags=["system"],
    )
    def infrastructure_status(
    ) -> dict[str, object]:
        return (
            infrastructure_factory()
            .get_status()
            .to_dictionary()
        )

    @app.get(
        "/api/workers/job/status",
        tags=["system"],
    )
    def job_worker_status(
    ) -> dict[str, object]:
        return (
            infrastructure_factory()
            .get_worker_status()
            .to_dictionary()
        )

    @app.get("/api/status", tags=["system"])
    def system_status() -> dict[str, object]:
        result = status_factory().get_status(
            request=SystemStatusRequest()
        )
        return result.to_dictionary()

    @app.get(
        "/api/run-history",
        tags=["operations"],
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
                "provider": request.provider,
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

    @app.get("/api/jobs", tags=["jobs"])
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

    @app.get("/api/jobs/{job_id}", tags=["jobs"])
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

    @app.get(
        "/api/research/latest",
        tags=["research"],
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
    )
    def news_summary() -> dict[str, object]:
        return research_factory().get_news_summary()

    @app.get(
        "/api/paper-trading/status",
        tags=["paper-trading"],
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
        "/api/portfolio",
        tags=["operations"],
    )
    def portfolio() -> dict[str, object]:
        return operations_factory().get_portfolio(
            request=OperationsQueryRequest()
        ).to_dictionary()

    @app.get(
        "/api/positions",
        tags=["operations"],
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
    )
    def risk_status() -> dict[str, object]:
        return operations_factory().get_risk_status(
            request=OperationsQueryRequest()
        ).to_dictionary()

    @app.get(
        "/api/reconciliation/latest",
        tags=["operations"],
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
