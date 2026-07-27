from app.application_errors import AuthenticationError
from app.authentication import AuthenticatedUser


class FakeAuthenticatedService:
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


def authenticated_client(app):
    from fastapi.testclient import TestClient

    client = TestClient(app)
    client.cookies.set("trading_session", "test-session")
    return client
