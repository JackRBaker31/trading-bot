from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    occurred_at: datetime
    action: str
    outcome: str
    username: str | None = None
    source_ip: str | None = None
    request_id: str | None = None
    target_id: str | None = None
    metadata: Mapping[str, Any] | None = None

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "occurred_at": (
                self.occurred_at.isoformat()
            ),
            "action": self.action,
            "outcome": self.outcome,
            "username": self.username,
            "source_ip": self.source_ip,
            "request_id": self.request_id,
            "target_id": self.target_id,
            "metadata": dict(
                self.metadata or {}
            ),
        }
