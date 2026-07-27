import pytest
from fastapi.testclient import TestClient

from app.application_errors import AuthenticationError
from web.app import create_app


class RejectingAuthenticationService:
    def authenticate(self, *, session_token):
        del session_token
        raise AuthenticationError(
            "Authentication is required.",
            code="AUTH_REQUIRED",
        )

    def verify_csrf(self, *, session_token, csrf_token):
        del session_token, csrf_token
        raise AuthenticationError(
            "Authentication is required.",
            code="AUTH_REQUIRED",
        )

    def login(self, **kwargs):
        del kwargs
        raise NotImplementedError

    def logout(self, **kwargs):
        del kwargs


PROTECTED_GET_ROUTES = (
    "/api/portfolio",
    "/api/positions",
    "/api/orders",
    "/api/orders/unresolved",
    "/api/risk/status",
    "/api/paper-trading/status",
    "/api/reconciliation/latest",
    "/api/status",
    "/api/run-history",
    "/api/jobs",
    "/api/jobs/example-job",
    "/api/news/signals",
    "/api/news/outcomes",
    "/api/news/summary",
    "/api/research/latest",
    "/api/intelligence/briefing",
    "/api/intelligence/snapshot",
    "/api/intelligence/graduation-status",
    "/api/shadow-performance",
    "/api/shadow-decisions",
    "/api/shadow-decisions/summary",
    "/api/infrastructure/status",
    "/api/workers/job/status",
)


@pytest.fixture
def unauthenticated_client() -> TestClient:
    return TestClient(
        create_app(
            authentication_service_factory=(
                lambda: RejectingAuthenticationService()
            )
        )
    )


@pytest.mark.parametrize("route", PROTECTED_GET_ROUTES)
def test_account_and_trading_routes_require_authentication(
    unauthenticated_client: TestClient,
    route: str,
) -> None:
    response = unauthenticated_client.get(route)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_health_routes_remain_public(
    unauthenticated_client: TestClient,
) -> None:
    assert unauthenticated_client.get("/health/live").status_code == 200


def test_cookie_secure_defaults_to_true(monkeypatch) -> None:
    from web.app import _cookie_secure

    monkeypatch.delenv("COOKIE_SECURE", raising=False)

    assert _cookie_secure() is True


def test_cookie_secure_can_be_explicitly_disabled_for_development(
    monkeypatch,
) -> None:
    from web.app import _cookie_secure

    monkeypatch.setenv("COOKIE_SECURE", "false")

    assert _cookie_secure() is False


def test_unlisted_replit_subdomain_is_not_trusted() -> None:
    client = TestClient(
        create_app(
            authentication_service_factory=(
                lambda: RejectingAuthenticationService()
            )
        )
    )

    response = client.options(
        "/api/status",
        headers={
            "Origin": "https://attacker.replit.app",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.headers.get(
        "access-control-allow-origin"
    ) is None
