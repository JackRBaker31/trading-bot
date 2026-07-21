import hashlib
import hmac
import secrets
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from typing import Callable
from uuid import uuid4

from app.application_errors import (
    AuthenticationError,
    AuthorizationError,
)
from app.authentication import (
    AuthenticatedUser,
    AuthenticationSession,
)
from app.auth_repository import (
    AuthenticationRepository,
)


class AuthenticationService:
    PASSWORD_PARAMETERS = {
        "n": 16_384,
        "r": 8,
        "p": 1,
        "dklen": 64,
    }

    def __init__(
        self,
        *,
        repository: AuthenticationRepository,
        session_duration: timedelta = timedelta(
            hours=8
        ),
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._session_duration = session_duration
        self._now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )

    def initialize(self) -> None:
        self._repository.initialize()

    def create_user(
        self,
        *,
        username: str,
        password: str,
        role: str = "ADMIN",
    ) -> AuthenticatedUser:
        cleaned_username = username.strip()
        cleaned_role = role.upper().strip()

        if len(cleaned_username) < 3:
            raise ValueError(
                "Username must contain at least "
                "three characters."
            )

        self._validate_password(password)

        salt = secrets.token_bytes(32)
        parameters = dict(
            self.PASSWORD_PARAMETERS
        )
        password_hash = self._hash_password(
            password=password,
            salt=salt,
            parameters=parameters,
        )

        return self._repository.create_user(
            user_id=str(uuid4()),
            username=cleaned_username,
            role=cleaned_role,
            password_salt=salt.hex(),
            password_hash=password_hash.hex(),
            password_parameters=parameters,
            created_at=self._utc_now(),
        )

    def login(
        self,
        *,
        username: str,
        password: str,
    ) -> AuthenticationSession:
        credentials = (
            self._repository
            .get_user_credentials(
                username=username.strip()
            )
        )

        if (
            credentials is None
            or not credentials["is_active"]
        ):
            raise AuthenticationError(
                "Invalid username or password.",
                code="AUTH_INVALID_CREDENTIALS",
            )

        actual_hash = self._hash_password(
            password=password,
            salt=bytes.fromhex(
                str(credentials["password_salt"])
            ),
            parameters=dict(
                credentials["password_parameters"]
            ),
        )

        if not hmac.compare_digest(
            actual_hash.hex(),
            str(credentials["password_hash"]),
        ):
            raise AuthenticationError(
                "Invalid username or password.",
                code="AUTH_INVALID_CREDENTIALS",
            )

        user = credentials["user"]
        assert isinstance(
            user,
            AuthenticatedUser,
        )

        session_token = secrets.token_urlsafe(48)
        csrf_token = secrets.token_urlsafe(32)
        now = self._utc_now()
        expires_at = now + self._session_duration

        self._repository.add_session(
            token_hash=self._token_hash(
                session_token
            ),
            user_id=user.user_id,
            csrf_token_hash=self._token_hash(
                csrf_token
            ),
            created_at=now,
            expires_at=expires_at,
        )

        return AuthenticationSession(
            session_token=session_token,
            csrf_token=csrf_token,
            user=user,
            expires_at=expires_at,
        )

    def authenticate(
        self,
        *,
        session_token: str | None,
    ) -> AuthenticatedUser:
        if not session_token:
            raise AuthenticationError(
                "Authentication is required.",
                code="AUTH_REQUIRED",
            )

        session = self._repository.get_session(
            token_hash=self._token_hash(
                session_token
            )
        )

        if (
            session is None
            or session["revoked_at"] is not None
            or not session["is_active"]
            or session["expires_at"] <= self._utc_now()
        ):
            raise AuthenticationError(
                "The login session is invalid or expired.",
                code="AUTH_SESSION_INVALID",
            )

        user = session["user"]
        assert isinstance(
            user,
            AuthenticatedUser,
        )
        return user

    def verify_csrf(
        self,
        *,
        session_token: str | None,
        csrf_token: str | None,
    ) -> AuthenticatedUser:
        user = self.authenticate(
            session_token=session_token
        )

        if not csrf_token:
            raise AuthorizationError(
                "A CSRF token is required.",
                code="CSRF_REQUIRED",
            )

        session = self._repository.get_session(
            token_hash=self._token_hash(
                session_token or ""
            )
        )
        assert session is not None

        if not hmac.compare_digest(
            str(session["csrf_token_hash"]),
            self._token_hash(csrf_token),
        ):
            raise AuthorizationError(
                "The CSRF token is invalid.",
                code="CSRF_INVALID",
            )

        return user

    def logout(
        self,
        *,
        session_token: str | None,
    ) -> None:
        if not session_token:
            return

        self._repository.revoke_session(
            token_hash=self._token_hash(
                session_token
            ),
            revoked_at=self._utc_now(),
        )

    @staticmethod
    def _validate_password(
        password: str,
    ) -> None:
        if len(password) < 12:
            raise ValueError(
                "Password must contain at least "
                "12 characters."
            )

        checks = (
            any(char.islower() for char in password),
            any(char.isupper() for char in password),
            any(char.isdigit() for char in password),
            any(
                not char.isalnum()
                for char in password
            ),
        )

        if not all(checks):
            raise ValueError(
                "Password must include lowercase, "
                "uppercase, numeric, and special "
                "characters."
            )

    @staticmethod
    def _hash_password(
        *,
        password: str,
        salt: bytes,
        parameters: dict[str, int],
    ) -> bytes:
        return hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=parameters["n"],
            r=parameters["r"],
            p=parameters["p"],
            dklen=parameters["dklen"],
        )

    @staticmethod
    def _token_hash(
        value: str,
    ) -> str:
        return hashlib.sha256(
            value.encode("utf-8")
        ).hexdigest()

    def _utc_now(
        self,
    ) -> datetime:
        value = self._now_provider()

        if value.tzinfo is None:
            raise ValueError(
                "Authentication clock must be "
                "timezone-aware."
            )

        return value.astimezone(
            timezone.utc
        )
