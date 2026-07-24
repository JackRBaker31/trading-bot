from fastapi.testclient import TestClient

from app.application_errors import (
    AuthenticationError,
)
from app.authentication import (
    AuthenticatedUser,
)
from app.copilot_models import (
    CopilotResponse,
    CopilotSuggestion,
)
from web.app import create_app
from datetime import (
    datetime,
    timezone,
)

from app.copilot_overview_models import (
    CopilotActivityOverview,
    CopilotFailuresOverview,
    CopilotOverview,
    CopilotPlatformOverview,
)
from app.copilot_intelligence_models import (
    CopilotGraduationOverview,
    CopilotIntelligenceOverview,
)


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

    def verify_csrf(
        self,
        *,
        session_token: str | None,
        csrf_token: str | None,
    ) -> AuthenticatedUser:
        del csrf_token
        return self.authenticate(
            session_token=session_token
        )

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


class FakeCopilotService:
    def __init__(self) -> None:
        self.questions: list[str] = []

    def answer(
        self,
        *,
        question: str,
    ) -> CopilotResponse:
        self.questions.append(question)

        return CopilotResponse(
            summary="KAIRO is operating normally.",
            suggestions=(
                CopilotSuggestion(
                    title="Platform health",
                    message=(
                        "All required services "
                        "are online."
                    ),
                    kind="success",
                ),
            ),
        )

    def operational_overview(
        self,
    ) -> CopilotResponse:
        return self.answer(
            question=(
                "Give me an operational overview."
            )
        )
        
    def dashboard_overview(
        self,
    ) -> CopilotOverview:
        return CopilotOverview(
            generated_at=datetime(
                2026,
                7,
                24,
                8,
                0,
                tzinfo=timezone.utc,
            ),
            overall_status="HEALTHY",
            platform=(
                CopilotPlatformOverview(
                    overall_status="HEALTHY",
                    online_services=5,
                    required_services=5,
                )
            ),
            activity=(
                CopilotActivityOverview(
                    running_jobs=0,
                    queued_jobs=0,
                )
            ),
            schedule=None,
            failures=(
                CopilotFailuresOverview(
                    recent_count=0,
                    latest=None,
                )
            ),
            trading_intelligence=(
                CopilotIntelligenceOverview(
                    trading_readiness="NOT_READY",
                    market_outlook="NEUTRAL",
                    confidence=0.0,
                    signal_count=0,
                    actionable_signal_count=0,
                    evidence_quality="UNKNOWN",
                )
            ),
            graduation=(
                CopilotGraduationOverview(
                    ready=False,
                    passed_checks=0,
                    total_checks=0,
                    checks=(),
                )
            ),
        )

def test_gets_copilot_overview(
) -> None:
    response = create_client(
        FakeCopilotService()
    ).get(
        "/api/copilot/overview"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["overall_status"]
        == "HEALTHY"
    )

    assert payload["platform"] == {
        "overall_status": "HEALTHY",
        "online_services": 5,
        "required_services": 5,
    }

    assert payload["activity"] == {
        "running_jobs": 0,
        "queued_jobs": 0,
        "active_jobs": 0,
    }

    assert payload["schedule"] is None

    assert payload["failures"] == {
        "recent_count": 0,
        "latest": None,
    }

    assert payload[
        "attention_items"
    ] == []
    
    assert payload["trading_intelligence"] == {
        "trading_readiness": "NOT_READY",
        "market_outlook": "NEUTRAL",
        "confidence": 0.0,
        "signal_count": 0,
        "actionable_signal_count": 0,
        "evidence_quality": "UNKNOWN",
    }

    assert payload["graduation"] == {
        "ready": False,
        "passed_checks": 0,
        "total_checks": 0,
        "failed_checks": 0,
        "checks": [],
    }

def create_client(
    service: FakeCopilotService,
    *,
    authenticated: bool = True,
) -> TestClient:
    client = TestClient(
        create_app(
            authentication_service_factory=(
                lambda: (
                    FakeAuthenticationService()
                )
            ),
            copilot_service_factory=(
                lambda: service
            ),
        )
    )

    if authenticated:
        client.cookies.set(
            "trading_session",
            "test-session",
        )

    return client


def test_lists_copilot_suggestions(
) -> None:
    response = create_client(
        FakeCopilotService()
    ).get(
        "/api/copilot/suggestions"
    )

    assert response.status_code == 200

    items = response.json()["items"]

    assert "Is KAIRO healthy?" in items
    assert "What failed recently?" in items
    assert "What happens next?" in items


def test_submits_copilot_question(
) -> None:
    service = FakeCopilotService()

    response = create_client(
        service
    ).post(
        "/api/copilot/query",
        json={
            "question": (
                "  Is   KAIRO healthy?  "
            ),
        },
    )

    assert response.status_code == 200

    assert service.questions == [
        "Is KAIRO healthy?"
    ]

    payload = response.json()

    assert payload["summary"] == (
        "KAIRO is operating normally."
    )

    assert payload["suggestions"][0] == {
        "title": "Platform health",
        "message": (
            "All required services "
            "are online."
        ),
        "kind": "success",
    }


def test_rejects_blank_copilot_question(
) -> None:
    response = create_client(
        FakeCopilotService()
    ).post(
        "/api/copilot/query",
        json={
            "question": "   ",
        },
    )

    assert response.status_code == 422


def test_copilot_requires_authentication(
) -> None:
    response = create_client(
        FakeCopilotService(),
        authenticated=False,
    ).post(
        "/api/copilot/query",
        json={
            "question": (
                "Is KAIRO healthy?"
            ),
        },
    )

    assert response.status_code == 401