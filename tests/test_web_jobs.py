from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.application_errors import (
    AuthenticationError,
    AuthorizationError,
)
from app.authentication import AuthenticatedUser
from app.job import (
    JobRecord,
    JobStatus,
    JobType,
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


class FakeStatusResult:
    def to_dictionary(self):
        return {"application_mode": "PAPER"}


class FakeStatusService:
    def get_status(self, *, request):
        del request
        return FakeStatusResult()


class FakeHistoryService:
    def initialize(self):
        pass

    def list_recent(self, **kwargs):
        del kwargs
        return ()


class FakeJobService:
    def __init__(self) -> None:
        self.enqueued: list[tuple] = []
        self.record = JobRecord(
            job_id="job-1",
            job_type=JobType.NEWS_RESEARCH_CYCLE,
            status=JobStatus.QUEUED,
            created_at=datetime.now(timezone.utc),
            payload={"symbols": ["AAPL"]},
        )

    def enqueue(self, *, job_type, payload):
        self.enqueued.append((job_type, payload))
        return JobRecord(
            job_id="job-1",
            job_type=job_type,
            status=JobStatus.QUEUED,
            created_at=datetime.now(timezone.utc),
            payload=payload,
        )

    def get(self, *, job_id):
        return self.record if job_id == "job-1" else None

    def list_recent(self, **kwargs):
        del kwargs
        return (self.record,)


def create_app_for_jobs(
    job_service: FakeJobService,
):
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
        job_service_factory=lambda: job_service,
    )


def create_client(
    job_service: FakeJobService,
) -> TestClient:
    client = TestClient(
        create_app_for_jobs(job_service)
    )
    client.cookies.set(
        "trading_session",
        "test-session",
    )
    client.headers.update(
        {"X-CSRF-Token": "test-csrf"}
    )
    return client


def test_queues_news_research_job() -> None:
    jobs = FakeJobService()
    response = create_client(jobs).post(
        "/api/jobs/news-research",
        json={
            "symbols": ["aapl", "MSFT"],
            "provider": "twelve_data",
            "max_price_requests": 5,
        },
    )

    assert response.status_code == 202
    assert response.json()["status"] == "QUEUED"
    job_type, payload = jobs.enqueued[0]
    assert job_type == JobType.NEWS_RESEARCH_CYCLE
    assert payload["symbols"] == ["AAPL", "MSFT"]
    assert payload["provider"] == "TWELVE_DATA"


def test_rejects_news_job_with_both_sources() -> None:
    response = create_client(FakeJobService()).post(
        "/api/jobs/news-research",
        json={
            "symbols": ["AAPL"],
            "watchlist": "data/watchlist.txt",
        },
    )

    assert response.status_code == 422


def test_queues_strategy_report_job() -> None:
    jobs = FakeJobService()
    response = create_client(jobs).post(
        "/api/jobs/strategy-report",
        json={"force": False},
    )

    assert response.status_code == 202
    assert jobs.enqueued[0][0] == (
        JobType.STRATEGY_REPORT
    )


def test_lists_and_reads_jobs() -> None:
    client = create_client(FakeJobService())

    listed = client.get("/api/jobs")
    found = client.get("/api/jobs/job-1")
    missing = client.get("/api/jobs/missing")

    assert listed.status_code == 200
    assert listed.json()["count"] == 1
    assert found.status_code == 200
    assert found.json()["job_id"] == "job-1"
    assert missing.status_code == 404


def test_job_queue_requires_authentication() -> None:
    client = TestClient(
        create_app_for_jobs(FakeJobService())
    )

    response = client.post(
        "/api/jobs/strategy-report",
        json={"force": False},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == (
        "AUTH_REQUIRED"
    )
