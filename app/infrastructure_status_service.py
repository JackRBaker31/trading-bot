from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from app.config import load_config
from app.infrastructure_status import (
    InfrastructureStatus,
    ServiceHealth,
)
from app.news_signal_store import NewsSignalStore
from app.worker_heartbeat_repository import (
    WorkerHeartbeatRepository,
)


class InfrastructureStatusService:
    def __init__(
        self,
        *,
        heartbeat_repository: WorkerHeartbeatRepository,
        config_path: str = "config.json",
        news_signal_store: NewsSignalStore | None = None,
        worker_name: str = "primary-job-worker",
        worker_stale_after_seconds: float = 30.0,
        news_stale_after_seconds: float = 24 * 60 * 60,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        if worker_stale_after_seconds <= 0:
            raise ValueError(
                "Worker stale threshold must be positive."
            )
        if news_stale_after_seconds <= 0:
            raise ValueError(
                "News stale threshold must be positive."
            )
        self._heartbeat_repository = heartbeat_repository
        self._config_path = config_path
        self._news_signal_store = (
            news_signal_store or NewsSignalStore()
        )
        self._worker_name = worker_name
        self._worker_stale_after_seconds = (
            worker_stale_after_seconds
        )
        self._news_stale_after_seconds = (
            news_stale_after_seconds
        )
        self._now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )

    def get_status(self) -> InfrastructureStatus:
        now = self._utc_now()
        config = load_config(self._config_path)
        services = (
            ServiceHealth(
                name="api",
                status="ONLINE",
                online=True,
                detail="FastAPI is responding.",
                last_updated_at=now,
            ),
            self._storage_health(now=now),
            self._worker_health(now=now),
            ServiceHealth(
                name="broker",
                status=(
                    "CONFIGURED"
                    if config.paper_trading.enabled
                    else "DISABLED"
                ),
                online=config.paper_trading.enabled,
                detail=(
                    f"Trading 212 {config.paper_trading.broker_environment} "
                    "is configured; this check does not contact the broker."
                ),
                last_updated_at=now,
                metadata={
                    "environment": config.paper_trading.broker_environment,
                    "execution_permission_confirmed": (
                        config.paper_trading
                        .order_execution_permission_confirmed
                    ),
                    "connection_verified": False,
                },
            ),
            ServiceHealth(
                name="market_data",
                status="CONFIGURED",
                online=True,
                detail=(
                    f"{config.market_data_provider} is the configured "
                    "market-data provider."
                ),
                last_updated_at=now,
                metadata={
                    "provider": config.market_data_provider,
                    "connection_verified": False,
                },
            ),
            self._news_health(now=now),
        )

        required_online = all(
            service.online
            for service in services
            if service.name in {
                "api",
                "storage",
                "job_worker",
            }
        )

        return InfrastructureStatus(
            generated_at=now,
            overall_status=(
                "HEALTHY"
                if required_online
                else "DEGRADED"
            ),
            services=services,
        )

    def get_worker_status(self) -> ServiceHealth:
        return self._worker_health(
            now=self._utc_now()
        )

    def _storage_health(
        self,
        *,
        now: datetime,
    ) -> ServiceHealth:
        online = self._heartbeat_repository.ping()
        return ServiceHealth(
            name="storage",
            status="HEALTHY" if online else "UNAVAILABLE",
            online=online,
            detail=(
                "SQLite application storage is readable."
                if online
                else "SQLite application storage is unavailable."
            ),
            last_updated_at=now,
        )

    def _worker_health(
        self,
        *,
        now: datetime,
    ) -> ServiceHealth:
        heartbeat = self._heartbeat_repository.get(
            worker_name=self._worker_name
        )
        if heartbeat is None:
            return ServiceHealth(
                name="job_worker",
                status="NOT_SEEN",
                online=False,
                detail="No job-worker heartbeat has been recorded.",
            )

        age_seconds = max(
            0.0,
            (
                now - heartbeat.last_heartbeat_at
            ).total_seconds(),
        )
        online = (
            heartbeat.status != "STOPPED"
            and age_seconds
            <= self._worker_stale_after_seconds
        )

        if not online:
            status = (
                "STOPPED"
                if heartbeat.status == "STOPPED"
                else "STALE"
            )
            detail = (
                "The job worker is stopped."
                if status == "STOPPED"
                else "The job-worker heartbeat is stale."
            )
        elif heartbeat.current_job_id:
            status = "BUSY"
            detail = (
                f"Processing {heartbeat.current_job_type}."
            )
        else:
            status = "IDLE"
            detail = "The job worker is online and waiting for work."

        return ServiceHealth(
            name="job_worker",
            status=status,
            online=online,
            detail=detail,
            last_updated_at=heartbeat.last_heartbeat_at,
            metadata={
                "worker_name": heartbeat.worker_name,
                "process_id": heartbeat.process_id,
                "heartbeat_age_seconds": round(
                    age_seconds,
                    2,
                ),
                "current_job_id": heartbeat.current_job_id,
                "current_job_type": heartbeat.current_job_type,
                "jobs_processed": heartbeat.jobs_processed,
                "started_at": heartbeat.started_at.isoformat(),
                "last_error": heartbeat.last_error,
            },
        )

    def _news_health(
        self,
        *,
        now: datetime,
    ) -> ServiceHealth:
        signals = self._news_signal_store.load_all()
        if not signals:
            return ServiceHealth(
                name="news",
                status="NO_DATA",
                online=False,
                detail="No news signals have been stored.",
            )

        latest = max(
            signal.published_at
            for signal in signals
        ).astimezone(timezone.utc)
        age_seconds = max(
            0.0,
            (now - latest).total_seconds(),
        )
        current = (
            age_seconds
            <= self._news_stale_after_seconds
        )
        return ServiceHealth(
            name="news",
            status="CURRENT" if current else "STALE",
            online=current,
            detail=(
                "Stored news signals are current."
                if current
                else "Stored news signals are stale."
            ),
            last_updated_at=latest,
            metadata={
                "signal_count": len(signals),
                "latest_signal_age_seconds": round(
                    age_seconds,
                    2,
                ),
            },
        )

    def _utc_now(self) -> datetime:
        value = self._now_provider()
        if value.tzinfo is None:
            raise ValueError(
                "Infrastructure clock must be timezone-aware."
            )
        return value.astimezone(timezone.utc)
