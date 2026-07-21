from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True)
class ServiceHealth:
    name: str
    status: str
    online: bool
    detail: str
    last_updated_at: datetime | None = None
    metadata: dict[str, object] | None = None

    def to_dictionary(self) -> dict[str, object]:
        payload = asdict(self)
        payload["last_updated_at"] = (
            None
            if self.last_updated_at is None
            else self.last_updated_at.isoformat()
        )
        payload["metadata"] = dict(
            self.metadata or {}
        )
        return payload


@dataclass(frozen=True)
class InfrastructureStatus:
    generated_at: datetime
    overall_status: str
    services: tuple[ServiceHealth, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "overall_status": self.overall_status,
            "services": {
                service.name: service.to_dictionary()
                for service in self.services
            },
        }
