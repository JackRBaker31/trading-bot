from fastapi.testclient import TestClient

from app.application_errors import (
    AuthenticationError,
    AuthorizationError,
)
from app.authentication import AuthenticatedUser
from app.paper_trading_process import (
    PaperTradingProcessState,
    PaperTradingProcessStatus,
)
from web.app import create_app


class FakeAuthenticationService:
    def __init__(self) -> None:
        self.user = AuthenticatedUser(
            user_id="user-1",
            username="admin",
            role="ADMIN",
        )

    def authenticate(
        self,
        *,
        session_token: str | None,
    ) -> AuthenticatedUser:
        if session_token != "test-session":
            raise AuthenticationError(
                "Authentication is required.",
                code="AUTH_REQUIRED",
            )

        return self.user

    def verify_csrf(
        self,
        *,
        session_token: str | None,
        csrf_token: str | None,
    ) -> AuthenticatedUser:
        user = self.authenticate(
            session_token=session_token
        )

        if csrf_token != "test-csrf":
            raise AuthorizationError(
                "The CSRF token is invalid.",
                code="CSRF_INVALID",
            )

        return user

    def login(
        self,
        *,
        username: str,
        password: str,
    ):
        del username, password
        raise NotImplementedError

    def logout(
        self,
        *,
        session_token: str | None,
    ) -> None:
        del session_token


class FakeAuditService:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def record(self, **kwargs):
        self.events.append(kwargs)
        return None

    def list_recent(
        self,
        *,
        limit: int = 100,
    ):
        del limit
        return tuple(self.events)


class FakePaperTradingController:
    def __init__(self) -> None:
        self.start_count = 0
        self.stop_count = 0

    def get_status(self):
        return PaperTradingProcessStatus(
            state=(
                PaperTradingProcessState.STOPPED
            ),
            process_id=None,
            lock_present=False,
            stop_requested=False,
        )

    def start(self):
        self.start_count += 1
        return PaperTradingProcessStatus(
            state=(
                PaperTradingProcessState.STARTING
            ),
            process_id=123,
            lock_present=False,
            stop_requested=False,
        )

    def stop(self):
        self.stop_count += 1
        return PaperTradingProcessStatus(
            state=(
                PaperTradingProcessState
                .STOP_REQUESTED
            ),
            process_id=123,
            lock_present=True,
            stop_requested=True,
        )


class FakeStatusService:
    def get_status(self, *, request):
        del request

        class Result:
            def to_dictionary(self):
                return {}

        return Result()


class FakeHistoryService:
    def initialize(self):
        pass

    def list_recent(self, **kwargs):
        del kwargs
        return ()


class FakeJobService:
    def list_recent(self, **kwargs):
        del kwargs
        return ()

    def get(self, **kwargs):
        del kwargs
        return None

    def enqueue(self, **kwargs):
        del kwargs
        raise AssertionError


class FakeResearchService:
    def get_latest_report(self):
        return None

    def list_signals(self, **kwargs):
        del kwargs
        raise AssertionError

    def list_outcomes(self, **kwargs):
        del kwargs
        raise AssertionError

    def get_news_summary(self):
        return {}


class FakeOperationsService:
    pass


def create_app_for_controller(controller):
    return create_app(
        authentication_service_factory=(
            lambda: FakeAuthenticationService()
        ),
        audit_service_factory=(
            lambda: FakeAuditService()
        ),
        system_status_service_factory=(
            lambda: FakeStatusService()
        ),
        run_history_service_factory=(
            lambda: FakeHistoryService()
        ),
        job_service_factory=(
            lambda: FakeJobService()
        ),
        research_query_service_factory=(
            lambda: FakeResearchService()
        ),
        operations_query_service_factory=(
            lambda: FakeOperationsService()
        ),
        paper_trading_controller_factory=(
            lambda: controller
        ),
    )


def create_client(controller) -> TestClient:
    client = TestClient(
        create_app_for_controller(controller)
    )
    client.cookies.set(
        "trading_session",
        "test-session",
    )
    client.headers.update(
        {"X-CSRF-Token": "test-csrf"}
    )
    return client


def test_returns_paper_trading_status() -> None:
    response = create_client(
        FakePaperTradingController()
    ).get(
        "/api/paper-trading/status"
    )

    assert response.status_code == 200
    assert response.json()["state"] == (
        "STOPPED"
    )


def test_starts_demo_paper_worker() -> None:
    controller = (
        FakePaperTradingController()
    )

    response = create_client(
        controller
    ).post(
        "/api/paper-trading/start",
        json={
            "confirm_demo_paper_trading": True
        },
    )

    assert response.status_code == 202
    assert response.json()["state"] == (
        "STARTING"
    )
    assert controller.start_count == 1


def test_start_requires_confirmation() -> None:
    response = create_client(
        FakePaperTradingController()
    ).post(
        "/api/paper-trading/start",
        json={
            "confirm_demo_paper_trading": False
        },
    )

    assert response.status_code == 422


def test_requests_graceful_stop() -> None:
    controller = (
        FakePaperTradingController()
    )

    response = create_client(
        controller
    ).post(
        "/api/paper-trading/stop",
        json={
            "confirm_stop": True
        },
    )

    assert response.status_code == 202
    assert response.json()["state"] == (
        "STOP_REQUESTED"
    )
    assert controller.stop_count == 1


def test_paper_trading_start_requires_authentication() -> None:
    client = TestClient(
        create_app_for_controller(
            FakePaperTradingController()
        )
    )

    response = client.post(
        "/api/paper-trading/start",
        json={
            "confirm_demo_paper_trading": True
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == (
        "AUTH_REQUIRED"
    )
