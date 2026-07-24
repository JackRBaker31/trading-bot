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