from datetime import (
    datetime,
    timezone,
)

from fastapi.testclient import TestClient

from app.application_errors import (
    AuthenticationError,
    DataStoreError,
)
from app.authentication import AuthenticatedUser
from app.run_history import (
    RunHistoryRecord,
    RunStatus,
    RunType,
)
from web.app import create_app


class FakeAuthenticationService:
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

        return AuthenticatedUser(
            user_id="user-1",
            username="admin",
            role="ADMIN",
        )

    def verify_csrf(self, **kwargs):
        return self.authenticate(
            session_token=kwargs.get("session_token")
        )

    def login(self, **kwargs):
        del kwargs
        raise NotImplementedError

    def logout(self, **kwargs) -> None:
        del kwargs


class FakeSystemStatusResult:
    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "application_mode": "PAPER",
            "market_data_provider": (
                "TWELVE_DATA"
            ),
            "real_money_trading_enabled": (
                False
            ),
        }


class FakeSystemStatusService:
    def __init__(
        self,
        *,
        error: Exception | None = None,
    ) -> None:
        self.error = error
        self.request_count = 0

    def get_status(
        self,
        *,
        request,
    ):
        del request
        self.request_count += 1

        if self.error is not None:
            raise self.error

        return FakeSystemStatusResult()


class FakeRunHistoryService:
    def __init__(self) -> None:
        self.initialize_count = 0
        self.requested_limit: int | None = None
        self.requested_type = None

    def initialize(self) -> None:
        self.initialize_count += 1

    def list_recent(
        self,
        *,
        limit: int = 50,
        run_type=None,
    ):
        self.requested_limit = limit
        self.requested_type = run_type

        return (
            RunHistoryRecord(
                run_id="run-1",
                run_type=(
                    RunType.STRATEGY_REPORT
                ),
                status=RunStatus.SUCCEEDED,
                started_at=datetime(
                    2026,
                    7,
                    19,
                    12,
                    0,
                    tzinfo=timezone.utc,
                ),
                finished_at=datetime(
                    2026,
                    7,
                    19,
                    12,
                    0,
                    5,
                    tzinfo=timezone.utc,
                ),
                created_count=6,
            ),
        )


def create_client(
    *,
    status_service=None,
    history_service=None,
) -> TestClient:
    status = (
        status_service
        or FakeSystemStatusService()
    )
    history = (
        history_service
        or FakeRunHistoryService()
    )

    app = create_app(
        authentication_service_factory=(
            lambda: FakeAuthenticationService()
        ),
        system_status_service_factory=(
            lambda: status
        ),
        run_history_service_factory=(
            lambda: history
        ),
    )
    client = TestClient(app)
    client.cookies.set(
        "trading_session",
        "test-session",
    )
    return client


def test_liveness_endpoint() -> None:
    response = create_client().get(
        "/health/live"
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok"
    }


def test_readiness_checks_local_services() -> None:
    status = FakeSystemStatusService()
    history = FakeRunHistoryService()
    client = create_client(
        status_service=status,
        history_service=history,
    )

    response = client.get(
        "/health/ready"
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready"
    }
    assert history.initialize_count == 1
    assert status.request_count == 1


def test_returns_system_status() -> None:
    response = create_client().get(
        "/api/status"
    )

    assert response.status_code == 200
    assert response.json()[
        "application_mode"
    ] == "PAPER"
    assert (
        response.json()[
            "real_money_trading_enabled"
        ]
        is False
    )


def test_returns_filtered_run_history() -> None:
    history = FakeRunHistoryService()
    client = create_client(
        history_service=history
    )

    response = client.get(
        "/api/run-history"
        "?limit=5"
        "&run_type=STRATEGY_REPORT"
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert (
        response.json()["items"][0][
            "run_id"
        ]
        == "run-1"
    )
    assert history.requested_limit == 5
    assert history.requested_type == (
        RunType.STRATEGY_REPORT
    )


def test_rejects_invalid_history_limit() -> None:
    response = create_client().get(
        "/api/run-history?limit=0"
    )

    assert response.status_code == 422


def test_application_error_is_sanitized() -> None:
    status = FakeSystemStatusService(
        error=DataStoreError(
            "Status could not be loaded.",
            code="STATUS_LOAD_FAILED",
            context={
                "secret_path": "hidden"
            },
        )
    )

    response = create_client(
        status_service=status
    ).get(
        "/api/status"
    )

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "STATUS_LOAD_FAILED",
            "message": (
                "Status could not be loaded."
            ),
            "retryable": False,
        }
    }
    assert "secret_path" not in (
        response.text
    )