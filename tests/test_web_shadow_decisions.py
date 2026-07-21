from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.application_errors import AuthenticationError, AuthorizationError
from app.authentication import AuthenticatedUser
from app.job import JobRecord, JobStatus, JobType
from web.app import create_app


class FakeAuthService:
    user = AuthenticatedUser(
        user_id="user-1", username="admin", role="ADMIN"
    )

    def authenticate(self, *, session_token):
        if session_token != "session":
            raise AuthenticationError(
                "Authentication is required.", code="AUTH_REQUIRED"
            )
        return self.user

    def verify_csrf(self, *, session_token, csrf_token):
        user = self.authenticate(session_token=session_token)
        if csrf_token != "csrf":
            raise AuthorizationError(
                "Invalid CSRF token.", code="CSRF_INVALID"
            )
        return user


class FakeAuditService:
    def record(self, **kwargs):
        return kwargs


class FakeJobService:
    def enqueue(self, *, job_type, payload):
        assert job_type is JobType.SHADOW_ANALYSIS
        return JobRecord(
            job_id="job-1",
            job_type=job_type,
            status=JobStatus.QUEUED,
            created_at=datetime.now(timezone.utc),
            payload=payload,
        )


class FakeShadowService:
    def list_decisions(self, **kwargs):
        return {
            "total_count": 1,
            "offset": kwargs["offset"],
            "limit": kwargs["limit"],
            "count": 1,
            "items": [{"decision_id": "decision-1"}],
        }

    def get_summary(self):
        return {
            "decision_count": 1,
            "trading_impact": "NONE",
        }


def create_client() -> TestClient:
    app = create_app(
        authentication_service_factory=lambda: FakeAuthService(),
        audit_service_factory=lambda: FakeAuditService(),
        job_service_factory=lambda: FakeJobService(),
        shadow_trading_service_factory=lambda: FakeShadowService(),
    )
    client = TestClient(app)
    client.cookies.set("trading_session", "session")
    client.headers.update({"X-CSRF-Token": "csrf"})
    return client


def test_queues_shadow_analysis() -> None:
    response = create_client().post(
        "/api/jobs/shadow-analysis",
        json={"force": False},
    )
    assert response.status_code == 202
    assert response.json()["job_type"] == "SHADOW_ANALYSIS"


def test_lists_shadow_decisions() -> None:
    response = create_client().get("/api/shadow-decisions")
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_returns_shadow_summary() -> None:
    response = create_client().get(
        "/api/shadow-decisions/summary"
    )
    assert response.status_code == 200
    assert response.json()["trading_impact"] == "NONE"
