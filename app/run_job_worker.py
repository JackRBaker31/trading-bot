import argparse
import os
import threading
import time
from datetime import datetime, timezone

from app.environment import load_environment
from app.job_crash_reporting import JobCrashReporter
from app.job_executor import JobExecutor
from app.job_recovery_service import JobRecoveryService
from app.job_repository import JobRepository
from app.job_service import JobService
from app.job_worker import JobWorker
from app.worker_heartbeat import WorkerHeartbeat
from web.dependencies import create_opportunity_ranking_service
from app.worker_heartbeat_repository import (
    WorkerHeartbeatRepository,
)


DEFAULT_DATABASE_PATH = "data/application.db"
DEFAULT_WORKER_NAME = "primary-job-worker"


def parse_args(
    argv: list[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process queued application jobs."
    )
    parser.add_argument(
        "--database",
        default=DEFAULT_DATABASE_PATH,
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process at most one job and exit.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=2.0,
    )
    parser.add_argument(
        "--heartbeat-seconds",
        type=float,
        default=5.0,
    )
    parser.add_argument(
        "--worker-name",
        default=DEFAULT_WORKER_NAME,
    )
    return parser.parse_args(argv)


def main() -> None:
    load_environment()
    args = parse_args()

    if args.poll_seconds <= 0:
        raise ValueError(
            "Poll interval must be positive."
        )
    if args.heartbeat_seconds <= 0:
        raise ValueError(
            "Heartbeat interval must be positive."
        )
    if not args.worker_name.strip():
        raise ValueError(
            "Worker name is required."
        )

    repository = JobRepository(
        database_path=args.database
    )
    service = JobService(
        repository=repository
    )
    service.initialize()
    recovery = JobRecoveryService(
        repository=repository
    ).reconcile()
    if recovery.reconciled_count:
        print(
            "JOB WORKER RECOVERED "
            f"{recovery.reconciled_count} "
            "ABANDONED JOB(S)"
        )

    crash_reporter = JobCrashReporter()
    worker = JobWorker(
        job_service=service,
        executor=JobExecutor(
            application_database_path=args.database,
            opportunity_ranking_runner=(
                lambda: create_opportunity_ranking_service(
                    database_path=args.database
                ).get_report(
                    capture_source="INTELLIGENCE_CYCLE"
                )
            ),
        ),
        crash_reporter=crash_reporter,
    )
    heartbeat_repository = (
        WorkerHeartbeatRepository(
            database_path=args.database
        )
    )
    heartbeat_repository.initialize()

    started_at = datetime.now(timezone.utc)
    process_id = os.getpid()
    stop_heartbeat = threading.Event()

    def write_heartbeat() -> None:
        heartbeat_repository.heartbeat(
            heartbeat=WorkerHeartbeat(
                worker_name=args.worker_name,
                process_id=process_id,
                status=(
                    "BUSY"
                    if worker.current_job_id
                    else "IDLE"
                ),
                started_at=started_at,
                last_heartbeat_at=datetime.now(
                    timezone.utc
                ),
                current_job_id=worker.current_job_id,
                current_job_type=(
                    worker.current_job_type
                ),
                jobs_processed=worker.jobs_processed,
                last_error=worker.last_error,
            )
        )

    def heartbeat_loop() -> None:
        while not stop_heartbeat.is_set():
            write_heartbeat()
            stop_heartbeat.wait(
                args.heartbeat_seconds
            )

    write_heartbeat()

    if args.once:
        try:
            processed = worker.run_once()
            write_heartbeat()
            print(
                "Processed one job."
                if processed
                else "No queued jobs."
            )
        finally:
            heartbeat_repository.mark_stopped(
                worker_name=args.worker_name,
                stopped_at=datetime.now(
                    timezone.utc
                ),
                jobs_processed=worker.jobs_processed,
                last_error=worker.last_error,
            )
        return

    thread = threading.Thread(
        target=heartbeat_loop,
        name="job-worker-heartbeat",
        daemon=True,
    )
    thread.start()
    print("JOB WORKER STARTED")

    try:
        while True:
            processed = worker.run_once()
            if not processed:
                time.sleep(args.poll_seconds)
    except KeyboardInterrupt:
        print("JOB WORKER STOPPING")
    finally:
        stop_heartbeat.set()
        thread.join(
            timeout=args.heartbeat_seconds + 1
        )
        heartbeat_repository.mark_stopped(
            worker_name=args.worker_name,
            stopped_at=datetime.now(
                timezone.utc
            ),
            jobs_processed=worker.jobs_processed,
            last_error=worker.last_error,
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise
    except BaseException as error:
        path = JobCrashReporter().report(
            error=error,
            job_id=None,
            job_type=None,
            stage="WORKER_MAIN",
        )
        print(f"JOB WORKER FATAL ERROR RECORDED: {path}")
        raise
