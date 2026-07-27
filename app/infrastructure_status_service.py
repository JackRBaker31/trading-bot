from datetime import datetime, timezone
from typing import Callable

from app.config import load_config
from app.infrastructure_status import (
    InfrastructureStatus,
    ServiceHealth,
)
from app.news_signal_store import NewsSignalStore
from app.supervisor_status_repository import SupervisorStatusRepository
from app.worker_heartbeat import WorkerHeartbeat
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
        scheduler_name: str = "primary-scheduler",
        worker_stale_after_seconds: float = 30.0,
        scheduler_stale_after_seconds: float = 30.0,
        news_stale_after_seconds: float = 24 * 60 * 60,
        supervisor_status_repository: SupervisorStatusRepository | None = None,
        supervisor_stale_after_seconds: float = 15.0,
        market_data_health_provider: Callable[[], dict[str, object]] | None = None,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        if worker_stale_after_seconds <= 0:
            raise ValueError(
                "Worker stale threshold must be positive."
            )
        if scheduler_stale_after_seconds <= 0:
            raise ValueError(
                "Scheduler stale threshold must be positive."
            )
        if supervisor_stale_after_seconds <= 0:
            raise ValueError(
                "Supervisor stale threshold must be positive."
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
        self._scheduler_name = scheduler_name
        self._worker_stale_after_seconds = (
            worker_stale_after_seconds
        )
        self._scheduler_stale_after_seconds = (
            scheduler_stale_after_seconds
        )
        self._news_stale_after_seconds = (
            news_stale_after_seconds
        )
        self._supervisor_status_repository = (
            supervisor_status_repository
            or SupervisorStatusRepository()
        )
        self._supervisor_stale_after_seconds = (
            supervisor_stale_after_seconds
        )
        self._market_data_health_provider = (
            market_data_health_provider
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
            self._supervisor_health(now=now),
            self._worker_health(now=now),
            self._scheduler_health(now=now),
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
            self._market_data_health(
                now=now,
                configured_provider=config.market_data_provider,
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
                "scheduler",
                "supervisor",
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

    def get_scheduler_status(self) -> ServiceHealth:
        return self._scheduler_health(
            now=self._utc_now()
        )


    def get_supervisor_status(self) -> ServiceHealth:
        return self._supervisor_health(now=self._utc_now())

    def _supervisor_health(
        self,
        *,
        now: datetime,
    ) -> ServiceHealth:
        repository = self._supervisor_status_repository
        try:
            snapshot = repository.load()
        except ValueError as error:
            return ServiceHealth(
                name="supervisor",
                status="FAILED",
                online=False,
                detail="Supervisor status could not be parsed.",
                last_updated_at=now,
                metadata={
                    "status_file": str(repository.status_path),
                    "error": str(error),
                },
            )

        if snapshot is None:
            return ServiceHealth(
                name="supervisor",
                status="NOT_SEEN",
                online=False,
                detail="No supervisor status has been recorded.",
                metadata={
                    "status_file": str(repository.status_path),
                },
            )

        age_seconds = max(
            0.0,
            (now - snapshot.generated_at).total_seconds(),
        )
        process_alive = repository.process_is_alive(
            snapshot.supervisor_process_id
        )
        processes = snapshot.processes
        managed_count = len(processes)
        failed_count = sum(
            1
            for process in processes
            if str(process.get("status", "")).upper() == "FAILED"
            or str(process.get("restart_state", "")).upper() == "FAILED"
        )
        recovering_states = {
            "FAULT_DETECTED",
            "RESTART_PENDING",
            "RESTARTING",
            "RECOVERING",
        }
        recovering_count = sum(
            1
            for process in processes
            if str(process.get("restart_state", "")).upper()
            in recovering_states
        )
        healthy_count = sum(
            1
            for process in processes
            if str(process.get("status", "")).upper() == "RUNNING"
            and str(process.get("restart_state", "HEALTHY")).upper()
            in {"HEALTHY", "RECOVERED"}
            and self._process_health_is_healthy(process)
        )

        recorded_status = snapshot.supervisor_status
        stale = age_seconds > self._supervisor_stale_after_seconds
        if recorded_status == "STOPPED":
            status = "STOPPED"
            online = False
            detail = "The KAIRO process supervisor is stopped."
        elif failed_count > 0:
            status = "FAILED"
            online = process_alive and not stale
            detail = (
                "One or more supervised services have entered "
                "restart lockout."
            )
        elif stale or not process_alive:
            status = "STALE"
            online = False
            detail = "The supervisor status is stale or its process is unavailable."
        elif recovering_count > 0 or healthy_count < managed_count:
            status = "DEGRADED"
            online = True
            detail = "The supervisor is running but one or more services are recovering."
        else:
            status = "RUNNING"
            online = True
            detail = (
                "KAIRO process supervision and automatic recovery are active."
            )

        return ServiceHealth(
            name="supervisor",
            status=status,
            online=online,
            detail=detail,
            last_updated_at=snapshot.generated_at,
            metadata={
                "process_id": snapshot.supervisor_process_id,
                "process_alive": process_alive,
                "restart_enabled": snapshot.restart_enabled,
                "managed_process_count": managed_count,
                "healthy_process_count": healthy_count,
                "recovering_process_count": recovering_count,
                "failed_process_count": failed_count,
                "status_age_seconds": round(age_seconds, 2),
                "status_file": str(repository.status_path),
            },
        )

    @staticmethod
    def _process_health_is_healthy(process: dict[str, object]) -> bool:
        health = process.get("health")
        if not isinstance(health, dict):
            return True
        return bool(health.get("healthy", False))


    def _market_data_health(
        self,
        *,
        now: datetime,
        configured_provider: str,
    ) -> ServiceHealth:
        provider = self._market_data_health_provider
        if provider is None:
            return ServiceHealth(
                name="market_data",
                status="CONFIGURED",
                online=True,
                detail=(
                    f"{configured_provider} is the configured "
                    "market-data provider."
                ),
                last_updated_at=now,
                metadata={
                    "provider": configured_provider,
                    "connection_verified": False,
                },
            )

        try:
            snapshot = provider()
        except Exception as error:
            return ServiceHealth(
                name="market_data",
                status="UNAVAILABLE",
                online=False,
                detail="Market-data resilience health could not be read.",
                last_updated_at=now,
                metadata={
                    "provider": configured_provider,
                    "error": str(error),
                },
            )

        status = str(snapshot.get("status", "UNKNOWN")).upper()
        circuit_state = str(
            snapshot.get("circuit_state", "UNKNOWN")
        ).upper()
        stale_fallbacks = int(snapshot.get("stale_fallbacks", 0) or 0)
        rate_limit_events = int(
            snapshot.get("rate_limit_events", 0) or 0
        )

        if status == "HEALTHY":
            detail = (
                "Market data is available with local caching, request "
                "deduplication and rate-budget protection."
            )
        elif circuit_state == "OPEN":
            detail = (
                "The provider circuit is open; KAIRO is serving cached "
                "historical data where available."
            )
        elif rate_limit_events > 0 or stale_fallbacks > 0:
            detail = (
                "Market data is degraded; cached historical data is "
                "keeping intelligence services available."
            )
        else:
            detail = (
                "Market data is unavailable and no suitable cached "
                "dataset could be supplied."
            )

        return ServiceHealth(
            name="market_data",
            status=status,
            online=status != "UNAVAILABLE",
            detail=detail,
            last_updated_at=now,
            metadata={
                **snapshot,
                "connection_verified": (
                    snapshot.get("last_success_at") is not None
                ),
            },
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
        return self._process_health(
            heartbeat=heartbeat,
            now=now,
            service_name="job_worker",
            display_name="job worker",
            stale_after_seconds=self._worker_stale_after_seconds,
            activity_label="Processing",
            processed_metadata_name="jobs_processed",
        )

    def _scheduler_health(
        self,
        *,
        now: datetime,
    ) -> ServiceHealth:
        heartbeat = self._heartbeat_repository.get(
            worker_name=self._scheduler_name
        )
        return self._process_health(
            heartbeat=heartbeat,
            now=now,
            service_name="scheduler",
            display_name="scheduler",
            stale_after_seconds=(
                self._scheduler_stale_after_seconds
            ),
            activity_label="Processing schedule",
            processed_metadata_name="tasks_processed",
        )

    @staticmethod
    def _process_health(
        *,
        heartbeat: WorkerHeartbeat | None,
        now: datetime,
        service_name: str,
        display_name: str,
        stale_after_seconds: float,
        activity_label: str,
        processed_metadata_name: str,
    ) -> ServiceHealth:
        if heartbeat is None:
            return ServiceHealth(
                name=service_name,
                status="NOT_SEEN",
                online=False,
                detail=(
                    f"No {display_name} heartbeat has been recorded."
                ),
            )

        age_seconds = max(
            0.0,
            (
                now - heartbeat.last_heartbeat_at
            ).total_seconds(),
        )
        online = (
            heartbeat.status != "STOPPED"
            and age_seconds <= stale_after_seconds
        )

        if not online:
            status = (
                "STOPPED"
                if heartbeat.status == "STOPPED"
                else "STALE"
            )
            detail = (
                f"The {display_name} is stopped."
                if status == "STOPPED"
                else f"The {display_name} heartbeat is stale."
            )
        elif heartbeat.current_job_id:
            status = "BUSY"
            detail = (
                f"{activity_label} "
                f"{heartbeat.current_job_type}."
            )
        else:
            status = "IDLE"
            detail = (
                f"The {display_name} is online and waiting for work."
            )

        metadata = {
            "worker_name": heartbeat.worker_name,
            "process_id": heartbeat.process_id,
            "heartbeat_age_seconds": round(
                age_seconds,
                2,
            ),
            "current_job_id": heartbeat.current_job_id,
            "current_job_type": heartbeat.current_job_type,
            processed_metadata_name: heartbeat.jobs_processed,
            "started_at": heartbeat.started_at.isoformat(),
            "last_error": heartbeat.last_error,
        }
        if service_name == "scheduler":
            metadata["current_schedule_id"] = (
                heartbeat.current_job_id
            )
            metadata["current_task_type"] = (
                heartbeat.current_job_type
            )

        return ServiceHealth(
            name=service_name,
            status=status,
            online=online,
            detail=detail,
            last_updated_at=heartbeat.last_heartbeat_at,
            metadata=metadata,
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
                "Infrastructure status requires timezone-aware time."
            )
        return value.astimezone(timezone.utc)