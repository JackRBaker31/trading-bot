from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    username: str
    role: str

    def to_dictionary(
        self,
    ) -> dict[str, str]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
        }


@dataclass(frozen=True)
class AuthenticationSession:
    session_token: str
    csrf_token: str
    user: AuthenticatedUser
    expires_at: datetime
