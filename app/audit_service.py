from datetime import (
    datetime,
    timezone,
)
from typing import Any, Mapping
from uuid import uuid4

from app.audit import AuditEvent
from app.auth_repository import (
    AuthenticationRepository,
)


class AuditService:
    def __init__(
        self,
        *,
        repository: AuthenticationRepository,
    ) -> None:
        self._repository = repository

    def record(
        self,
        *,
        action: str,
        outcome: str,
        username: str | None = None,
        source_ip: str | None = None,
        request_id: str | None = None,
        target_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=str(uuid4()),
            occurred_at=datetime.now(
                timezone.utc
            ),
            action=action.upper().strip(),
            outcome=outcome.upper().strip(),
            username=username,
            source_ip=source_ip,
            request_id=request_id,
            target_id=target_id,
            metadata=dict(metadata or {}),
        )

        self._repository.add_audit_event(
            event=event.to_dictionary()
        )
        return event

    def list_recent(
        self,
        *,
        limit: int = 100,
    ) -> tuple[dict[str, object], ...]:
        if limit <= 0:
            raise ValueError(
                "Audit limit must be positive."
            )

        return self._repository.list_audit_events(
            limit=limit
        )
