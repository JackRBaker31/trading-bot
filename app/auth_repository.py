import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.application_errors import (
    DataStoreError,
)
from app.authentication import (
    AuthenticatedUser,
)


class AuthenticationRepository:
    def __init__(
        self,
        *,
        database_path: str,
    ) -> None:
        cleaned = database_path.strip()

        if not cleaned:
            raise ValueError(
                "Authentication database path is required."
            )

        self._database_path = Path(cleaned)

    def initialize(self) -> None:
        try:
            self._database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with self._connect() as connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS app_users (
                        user_id TEXT PRIMARY KEY,
                        username TEXT NOT NULL UNIQUE,
                        role TEXT NOT NULL,
                        password_salt TEXT NOT NULL,
                        password_hash TEXT NOT NULL,
                        password_parameters_json TEXT NOT NULL,
                        is_active INTEGER NOT NULL,
                        created_at TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS auth_sessions (
                        token_hash TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        csrf_token_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        revoked_at TEXT,
                        FOREIGN KEY(user_id)
                            REFERENCES app_users(user_id)
                    );

                    CREATE INDEX IF NOT EXISTS
                    idx_auth_sessions_user_id
                    ON auth_sessions(user_id);

                    CREATE TABLE IF NOT EXISTS audit_events (
                        event_id TEXT PRIMARY KEY,
                        occurred_at TEXT NOT NULL,
                        action TEXT NOT NULL,
                        outcome TEXT NOT NULL,
                        username TEXT,
                        source_ip TEXT,
                        request_id TEXT,
                        target_id TEXT,
                        metadata_json TEXT NOT NULL
                    );

                    CREATE INDEX IF NOT EXISTS
                    idx_audit_events_occurred_at
                    ON audit_events(occurred_at DESC);
                    """
                )
        except sqlite3.Error as error:
            raise DataStoreError(
                "Authentication storage could not "
                "be initialized.",
                code="AUTH_STORAGE_INITIALIZE_FAILED",
            ) from error

    def create_user(
        self,
        *,
        user_id: str,
        username: str,
        role: str,
        password_salt: str,
        password_hash: str,
        password_parameters: dict[str, int],
        created_at: datetime,
    ) -> AuthenticatedUser:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO app_users (
                        user_id,
                        username,
                        role,
                        password_salt,
                        password_hash,
                        password_parameters_json,
                        is_active,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        user_id,
                        username,
                        role,
                        password_salt,
                        password_hash,
                        json.dumps(
                            password_parameters,
                            sort_keys=True,
                        ),
                        created_at.isoformat(),
                    ),
                )
        except sqlite3.IntegrityError as error:
            raise DataStoreError(
                "A user with this username "
                "already exists.",
                code="AUTH_USER_ALREADY_EXISTS",
                context={"username": username},
            ) from error
        except sqlite3.Error as error:
            raise DataStoreError(
                "The user could not be created.",
                code="AUTH_USER_CREATE_FAILED",
            ) from error

        return AuthenticatedUser(
            user_id=user_id,
            username=username,
            role=role,
        )

    def get_user_credentials(
        self,
        *,
        username: str,
    ) -> dict[str, object] | None:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT *
                    FROM app_users
                    WHERE username = ?
                    """,
                    (username,),
                ).fetchone()
        except sqlite3.Error as error:
            raise DataStoreError(
                "User credentials could not be loaded.",
                code="AUTH_USER_LOAD_FAILED",
            ) from error

        if row is None:
            return None

        return {
            "user": AuthenticatedUser(
                user_id=row["user_id"],
                username=row["username"],
                role=row["role"],
            ),
            "password_salt": row["password_salt"],
            "password_hash": row["password_hash"],
            "password_parameters": json.loads(
                row["password_parameters_json"]
            ),
            "is_active": bool(row["is_active"]),
        }

    def add_session(
        self,
        *,
        token_hash: str,
        user_id: str,
        csrf_token_hash: str,
        created_at: datetime,
        expires_at: datetime,
    ) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO auth_sessions (
                        token_hash,
                        user_id,
                        csrf_token_hash,
                        created_at,
                        expires_at,
                        revoked_at
                    )
                    VALUES (?, ?, ?, ?, ?, NULL)
                    """,
                    (
                        token_hash,
                        user_id,
                        csrf_token_hash,
                        created_at.isoformat(),
                        expires_at.isoformat(),
                    ),
                )
        except sqlite3.Error as error:
            raise DataStoreError(
                "The login session could not be saved.",
                code="AUTH_SESSION_SAVE_FAILED",
            ) from error

    def get_session(
        self,
        *,
        token_hash: str,
    ) -> dict[str, object] | None:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT
                        auth_sessions.*,
                        app_users.username,
                        app_users.role,
                        app_users.is_active
                    FROM auth_sessions
                    JOIN app_users
                        ON app_users.user_id =
                           auth_sessions.user_id
                    WHERE token_hash = ?
                    """,
                    (token_hash,),
                ).fetchone()
        except sqlite3.Error as error:
            raise DataStoreError(
                "The login session could not be loaded.",
                code="AUTH_SESSION_LOAD_FAILED",
            ) from error

        if row is None:
            return None

        return {
            "user": AuthenticatedUser(
                user_id=row["user_id"],
                username=row["username"],
                role=row["role"],
            ),
            "csrf_token_hash": row["csrf_token_hash"],
            "expires_at": datetime.fromisoformat(
                row["expires_at"]
            ),
            "revoked_at": (
                None
                if row["revoked_at"] is None
                else datetime.fromisoformat(
                    row["revoked_at"]
                )
            ),
            "is_active": bool(row["is_active"]),
        }

    def revoke_session(
        self,
        *,
        token_hash: str,
        revoked_at: datetime,
    ) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE auth_sessions
                    SET revoked_at = ?
                    WHERE token_hash = ?
                    """,
                    (
                        revoked_at.isoformat(),
                        token_hash,
                    ),
                )
        except sqlite3.Error as error:
            raise DataStoreError(
                "The login session could not be revoked.",
                code="AUTH_SESSION_REVOKE_FAILED",
            ) from error

    def add_audit_event(
        self,
        *,
        event: dict[str, object],
    ) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO audit_events (
                        event_id,
                        occurred_at,
                        action,
                        outcome,
                        username,
                        source_ip,
                        request_id,
                        target_id,
                        metadata_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event["event_id"],
                        event["occurred_at"],
                        event["action"],
                        event["outcome"],
                        event["username"],
                        event["source_ip"],
                        event["request_id"],
                        event["target_id"],
                        json.dumps(
                            event["metadata"],
                            sort_keys=True,
                        ),
                    ),
                )
        except sqlite3.Error as error:
            raise DataStoreError(
                "The audit event could not be saved.",
                code="AUDIT_EVENT_SAVE_FAILED",
            ) from error

    def list_audit_events(
        self,
        *,
        limit: int,
    ) -> tuple[dict[str, object], ...]:
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM audit_events
                    ORDER BY occurred_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        except sqlite3.Error as error:
            raise DataStoreError(
                "Audit events could not be loaded.",
                code="AUDIT_EVENT_LOAD_FAILED",
            ) from error

        return tuple(
            {
                "event_id": row["event_id"],
                "occurred_at": row["occurred_at"],
                "action": row["action"],
                "outcome": row["outcome"],
                "username": row["username"],
                "source_ip": row["source_ip"],
                "request_id": row["request_id"],
                "target_id": row["target_id"],
                "metadata": json.loads(
                    row["metadata_json"]
                ),
            }
            for row in rows
        )

    def _connect(
        self,
    ) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._database_path
        )
        connection.row_factory = sqlite3.Row
        return connection
