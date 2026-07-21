import argparse
import os
import threading
import time
from datetime import datetime, timezone

from app.environment import load_environment
from app.job_repository import JobRepository
from app.job_service import JobService
from app.scheduled_task_repository import ScheduledTaskRepository
from app.scheduler_service import SchedulerService
from app.worker_heartbeat import WorkerHeartbeat
from app.worker_heartbeat_repository import WorkerHeartbeatRepository


DEFAULT_DATABASE_PATH = "data/application.db"
DEFAULT_WORKER_NAME = "primary-scheduler"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enqueue due scheduled tasks.")
    parser.add_argument("--database", default=DEFAULT_DATABASE_PATH)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    parser.add_argument("--heartbeat-seconds", type=float, default=5.0)
    parser.add_argument("--claim-seconds", type=int, default=60)
    parser.add_argument("--worker-name", default=DEFAULT_WORKER_NAME)
    return parser.parse_args(argv)


def main() -> None:
    load_environment()
    args = parse_args()
    if args.poll_seconds <= 0 or args.heartbeat_seconds <= 0:
        raise ValueError("Scheduler intervals must be positive.")
    if args.claim_seconds <= 0:
        raise ValueError("Scheduler claim duration must be positive.")
    if not args.worker_name.strip():
        raise ValueError("Scheduler worker name is required.")

    service = SchedulerService(
        schedule_repository=ScheduledTaskRepository(database_path=args.database),
        job_service=JobService(repository=JobRepository(database_path=args.database)),
        claim_seconds=args.claim_seconds,
    )
    service.initialize()

    heartbeats = WorkerHeartbeatRepository(database_path=args.database)
    heartbeats.initialize()
    started_at = datetime.now(timezone.utc)
    process_id = os.getpid()
    stop_heartbeat = threading.Event()

    def write_heartbeat() -> None:
        heartbeats.heartbeat(
            heartbeat=WorkerHeartbeat(
                worker_name=args.worker_name,
                process_id=process_id,
                status="BUSY" if service.current_schedule_id else "IDLE",
                started_at=started_at,
                last_heartbeat_at=datetime.now(timezone.utc),
                current_job_id=service.current_schedule_id,
                current_job_type=service.current_task_type,
                jobs_processed=service.tasks_processed,
                last_error=service.last_error,
            )
        )

    def heartbeat_loop() -> None:
        while not stop_heartbeat.is_set():
            write_heartbeat()
            stop_heartbeat.wait(args.heartbeat_seconds)

    write_heartbeat()
    if args.once:
        try:
            processed = service.run_once()
            write_heartbeat()
            print("Processed one schedule." if processed else "No due schedules.")
        finally:
            heartbeats.mark_stopped(
                worker_name=args.worker_name,
                stopped_at=datetime.now(timezone.utc),
                jobs_processed=service.tasks_processed,
                last_error=service.last_error,
            )
        return

    thread = threading.Thread(target=heartbeat_loop, name="scheduler-heartbeat", daemon=True)
    thread.start()
    print("SCHEDULER STARTED")
    try:
        while True:
            try:
                processed = service.run_once()
            except Exception as error:
                print(f"SCHEDULER ERROR: {type(error).__name__}")
                processed = False
            if not processed:
                time.sleep(args.poll_seconds)
    except KeyboardInterrupt:
        print("SCHEDULER STOPPING")
    finally:
        stop_heartbeat.set()
        thread.join(timeout=args.heartbeat_seconds + 1)
        heartbeats.mark_stopped(
            worker_name=args.worker_name,
            stopped_at=datetime.now(timezone.utc),
            jobs_processed=service.tasks_processed,
            last_error=service.last_error,
        )


if __name__ == "__main__":
    main()