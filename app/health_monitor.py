from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from app.worker_heartbeat import WorkerHeartbeat
from app.worker_heartbeat_repository import WorkerHeartbeatRepository


UtcNow = Callable[[], datetime]
MonotonicClock = Callable[[], float]
HttpProbe = Callable[[str, float], tuple[bool, float | None, str]]


class HeartbeatReader(Protocol):
    def get(self, *, worker_name: str) -> WorkerHeartbeat | None: ...


@dataclass(frozen=True)
class HealthMonitorConfig:
    api_url: str = "http://127.0.0.1:8000/health/ready"
    api_timeout_seconds: float = 2.0
    startup_grace_seconds: float = 15.0
    heartbeat_stale_seconds: float = 20.0
    persistent_failure_count: int = 3
    job_worker_name: str = "primary-job-worker"
    scheduler_name: str = "primary-scheduler"

    def __post_init__(self) -> None:
        if not self.api_url.strip():
            raise ValueError("API health-check URL is required.")
        if self.api_timeout_seconds <= 0:
            raise ValueError("API health-check timeout must be positive.")
        if self.startup_grace_seconds < 0:
            raise ValueError("Startup grace cannot be negative.")
        if self.heartbeat_stale_seconds <= 0:
            raise ValueError("Heartbeat stale threshold must be positive.")
        if self.persistent_failure_count <= 0:
            raise ValueError("Persistent failure count must be positive.")
        if not self.job_worker_name.strip():
            raise ValueError("Job-worker heartbeat name is required.")
        if not self.scheduler_name.strip():
            raise ValueError("Scheduler heartbeat name is required.")


@dataclass(frozen=True)
class ServiceHealth:
    name: str
    health_status: str
    healthy: bool
    persistent_fault: bool
    consecutive_health_failures: int
    last_health_check_at: str
    last_healthy_at: str | None
    health_detail: str
    response_time_ms: float | None = None
    heartbeat_age_seconds: float | None = None
    heartbeat_status: str | None = None
    heartbeat_process_id: int | None = None
    heartbeat_last_error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class _ServiceState:
    consecutive_failures: int = 0
    last_healthy_at: datetime | None = None


class HealthMonitor:
    """Observe KAIRO service health without restarting any process."""

    def __init__(
        self,
        *,
        heartbeat_repository: HeartbeatReader | None = None,
        config: HealthMonitorConfig | None = None,
        utc_now: UtcNow | None = None,
        monotonic_clock: MonotonicClock = time.monotonic,
        http_probe: HttpProbe | None = None,
    ) -> None:
        self._config = config or HealthMonitorConfig()
        self._heartbeat_repository = (
            heartbeat_repository or WorkerHeartbeatRepository()
        )
        self._utc_now = utc_now or (lambda: datetime.now(timezone.utc))
        self._monotonic_clock = monotonic_clock
        self._http_probe = http_probe or _default_http_probe
        self._started_monotonic = self._monotonic_clock()
        self._states = {
            "api": _ServiceState(),
            "job_worker": _ServiceState(),
            "scheduler": _ServiceState(),
        }
        self._latest: dict[str, ServiceHealth] = {}

    def check_all(self) -> dict[str, ServiceHealth]:
        now = _as_utc(self._utc_now())
        in_startup_grace = (
            self._monotonic_clock() - self._started_monotonic
            < self._config.startup_grace_seconds
        )

        results = {
            "api": self._check_api(now=now, in_startup_grace=in_startup_grace),
            "job_worker": self._check_heartbeat_service(
                name="job_worker",
                worker_name=self._config.job_worker_name,
                now=now,
                in_startup_grace=in_startup_grace,
            ),
            "scheduler": self._check_heartbeat_service(
                name="scheduler",
                worker_name=self._config.scheduler_name,
                now=now,
                in_startup_grace=in_startup_grace,
            ),
        }
        self._latest = results
        return dict(results)

    def latest(self) -> dict[str, ServiceHealth]:
        return dict(self._latest)

    def _check_api(
        self,
        *,
        now: datetime,
        in_startup_grace: bool,
    ) -> ServiceHealth:
        try:
            healthy, response_time_ms, detail = self._http_probe(
                self._config.api_url,
                self._config.api_timeout_seconds,
            )
        except Exception as error:  # Defensive boundary around injected probes.
            healthy = False
            response_time_ms = None
            detail = f"API health probe failed: {type(error).__name__}."

        if healthy:
            return self._record(
                name="api",
                now=now,
                health_status="HEALTHY",
                healthy=True,
                detail=detail or "API readiness endpoint is healthy.",
                response_time_ms=response_time_ms,
            )

        if in_startup_grace:
            return self._record_starting(
                name="api",
                now=now,
                detail="API is within its startup grace period.",
                response_time_ms=response_time_ms,
            )

        return self._record(
            name="api",
            now=now,
            health_status="UNREACHABLE",
            healthy=False,
            detail=detail or "API readiness endpoint could not be reached.",
            response_time_ms=response_time_ms,
        )

    def _check_heartbeat_service(
        self,
        *,
        name: str,
        worker_name: str,
        now: datetime,
        in_startup_grace: bool,
    ) -> ServiceHealth:
        try:
            heartbeat = self._heartbeat_repository.get(worker_name=worker_name)
        except Exception as error:
            if in_startup_grace:
                return self._record_starting(
                    name=name,
                    now=now,
                    detail=f"{name} heartbeat storage is not ready.",
                )
            return self._record(
                name=name,
                now=now,
                health_status="UNREACHABLE",
                healthy=False,
                detail=(
                    f"{name} heartbeat could not be read: "
                    f"{type(error).__name__}."
                ),
            )

        if heartbeat is None:
            if in_startup_grace:
                return self._record_starting(
                    name=name,
                    now=now,
                    detail=f"Waiting for the {name} heartbeat.",
                )
            return self._record(
                name=name,
                now=now,
                health_status="NOT_SEEN",
                healthy=False,
                detail=f"The {name} heartbeat has not been recorded.",
            )

        heartbeat_at = _as_utc(heartbeat.last_heartbeat_at)
        heartbeat_age = max(0.0, (now - heartbeat_at).total_seconds())
        heartbeat_status = heartbeat.status.upper().strip()
        common = {
            "heartbeat_age_seconds": round(heartbeat_age, 2),
            "heartbeat_status": heartbeat_status,
            "heartbeat_process_id": heartbeat.process_id,
            "heartbeat_last_error": heartbeat.last_error,
        }

        if heartbeat_status == "STOPPED":
            return self._record(
                name=name,
                now=now,
                health_status="STOPPED",
                healthy=False,
                detail=f"The {name} reported a clean stop.",
                **common,
            )

        if heartbeat_age > self._config.heartbeat_stale_seconds:
            return self._record(
                name=name,
                now=now,
                health_status="STALE",
                healthy=False,
                detail=(
                    f"The {name} heartbeat is {heartbeat_age:.1f} seconds old; "
                    f"the threshold is {self._config.heartbeat_stale_seconds:.1f} seconds."
                ),
                **common,
            )

        if heartbeat_status not in {"IDLE", "BUSY", "STARTING"}:
            return self._record(
                name=name,
                now=now,
                health_status="UNHEALTHY",
                healthy=False,
                detail=f"The {name} reported unexpected state {heartbeat_status}.",
                **common,
            )

        return self._record(
            name=name,
            now=now,
            health_status="HEALTHY",
            healthy=True,
            detail=f"The {name} heartbeat is fresh ({heartbeat_status}).",
            **common,
        )

    def _record_starting(
        self,
        *,
        name: str,
        now: datetime,
        detail: str,
        response_time_ms: float | None = None,
    ) -> ServiceHealth:
        state = self._states[name]
        return ServiceHealth(
            name=name,
            health_status="STARTING",
            healthy=False,
            persistent_fault=False,
            consecutive_health_failures=state.consecutive_failures,
            last_health_check_at=now.isoformat(),
            last_healthy_at=(
                None
                if state.last_healthy_at is None
                else state.last_healthy_at.isoformat()
            ),
            health_detail=detail,
            response_time_ms=response_time_ms,
        )

    def _record(
        self,
        *,
        name: str,
        now: datetime,
        health_status: str,
        healthy: bool,
        detail: str,
        response_time_ms: float | None = None,
        heartbeat_age_seconds: float | None = None,
        heartbeat_status: str | None = None,
        heartbeat_process_id: int | None = None,
        heartbeat_last_error: str | None = None,
    ) -> ServiceHealth:
        state = self._states[name]
        if healthy:
            state.consecutive_failures = 0
            state.last_healthy_at = now
        else:
            state.consecutive_failures += 1

        return ServiceHealth(
            name=name,
            health_status=health_status,
            healthy=healthy,
            persistent_fault=(
                not healthy
                and state.consecutive_failures
                >= self._config.persistent_failure_count
            ),
            consecutive_health_failures=state.consecutive_failures,
            last_health_check_at=now.isoformat(),
            last_healthy_at=(
                None
                if state.last_healthy_at is None
                else state.last_healthy_at.isoformat()
            ),
            health_detail=detail,
            response_time_ms=response_time_ms,
            heartbeat_age_seconds=heartbeat_age_seconds,
            heartbeat_status=heartbeat_status,
            heartbeat_process_id=heartbeat_process_id,
            heartbeat_last_error=heartbeat_last_error,
        )


def _default_http_probe(
    url: str,
    timeout_seconds: float,
) -> tuple[bool, float | None, str]:
    started = time.perf_counter()
    try:
        with urlopen(url, timeout=timeout_seconds) as response:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            status = int(response.status)
            if 200 <= status < 300:
                return True, round(elapsed_ms, 2), "API readiness endpoint is healthy."
            return (
                False,
                round(elapsed_ms, 2),
                f"API readiness endpoint returned HTTP {status}.",
            )
    except HTTPError as error:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return (
            False,
            round(elapsed_ms, 2),
            f"API readiness endpoint returned HTTP {error.code}.",
        )
    except (TimeoutError, URLError, OSError, ValueError) as error:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return (
            False,
            round(elapsed_ms, 2),
            f"API readiness endpoint is unreachable: {type(error).__name__}.",
        )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)