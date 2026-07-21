from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True)
class WorkerHeartbeat:
    worker_name: str
    process_id: int
    status: str
    started_at: datetime
    last_heartbeat_at: datetime
    current_job_id: str | None
    current_job_type: str | None
    jobs_processed: int
    last_error: str | None = None
    stopped_at: datetime | None = None

    def to_dictionary(self) -> dict[str, object]:
        payload = asdict(self)
        for key in (
            "started_at",
            "last_heartbeat_at",
            "stopped_at",
        ):
            value = payload[key]
            payload[key] = (
                None
                if value is None
                else value.isoformat()
            )
        return payload
