from datetime import timedelta

import pytest

from app.application_errors import (
    AuthenticationError,
    AuthorizationError,
)
from app.auth_repository import (
    AuthenticationRepository,
)
from app.auth_service import (
    AuthenticationService,
)


def create_service(
    tmp_path,
) -> AuthenticationService:
    service = AuthenticationService(
        repository=AuthenticationRepository(
            database_path=str(
                tmp_path / "application.db"
            )
        ),
        session_duration=timedelta(
            hours=1
        ),
    )
    service.initialize()
    return service


def test_creates_user_and_authenticates(
    tmp_path,
) -> None:
    service = create_service(tmp_path)
    service.create_user(
        username="admin",
        password="StrongPassword1!",
    )

    session = service.login(
        username="admin",
        password="StrongPassword1!",
    )

    user = service.authenticate(
        session_token=session.session_token
    )
    assert user.username == "admin"

    csrf_user = service.verify_csrf(
        session_token=session.session_token,
        csrf_token=session.csrf_token,
    )
    assert csrf_user.user_id == user.user_id


def test_rejects_invalid_password(
    tmp_path,
) -> None:
    service = create_service(tmp_path)
    service.create_user(
        username="admin",
        password="StrongPassword1!",
    )

    with pytest.raises(
        AuthenticationError,
    ):
        service.login(
            username="admin",
            password="wrong",
        )


def test_rejects_invalid_csrf(
    tmp_path,
) -> None:
    service = create_service(tmp_path)
    service.create_user(
        username="admin",
        password="StrongPassword1!",
    )
    session = service.login(
        username="admin",
        password="StrongPassword1!",
    )

    with pytest.raises(
        AuthorizationError,
    ):
        service.verify_csrf(
            session_token=session.session_token,
            csrf_token="incorrect",
        )


def test_logout_revokes_session(
    tmp_path,
) -> None:
    service = create_service(tmp_path)
    service.create_user(
        username="admin",
        password="StrongPassword1!",
    )
    session = service.login(
        username="admin",
        password="StrongPassword1!",
    )
    service.logout(
        session_token=session.session_token
    )

    with pytest.raises(
        AuthenticationError,
    ):
        service.authenticate(
            session_token=session.session_token
        )
