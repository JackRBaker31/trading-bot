import sqlite3
from datetime import datetime
from pathlib import Path

from app.application_errors import DataStoreError
from app.worker_heartbeat import WorkerHeartbeat


class WorkerHeartbeatRepository:
    def __init__(
        self,
        *,
        database_path: str = "data/application.db",
    ) -> None:
        cleaned = database_path.strip()
        if not cleaned:
            raise ValueError(
                "Worker-heartbeat database path is required."
            )
        self._database_path = Path(cleaned)

    def initialize(self) -> None:
        try:
            self._database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            with self._connect() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS worker_heartbeats (
                        worker_name TEXT PRIMARY KEY,
                        process_id INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        started_at TEXT NOT NULL,
                        last_heartbeat_at TEXT NOT NULL,
                        current_job_id TEXT,
                        current_job_type TEXT,
                        jobs_processed INTEGER NOT NULL,
                        last_error TEXT,
                        stopped_at TEXT
                    )
                    """
                )
        except sqlite3.Error as error:
            raise DataStoreError(
                "Worker-heartbeat storage could not be initialized.",
                code="WORKER_HEARTBEAT_INITIALIZE_FAILED",
            ) from error

    def register(
        self,
        *,
        heartbeat: WorkerHeartbeat,
    ) -> None:
        self._upsert(heartbeat=heartbeat)

    def heartbeat(
        self,
        *,
        heartbeat: WorkerHeartbeat,
    ) -> None:
        self._upsert(heartbeat=heartbeat)

    def mark_stopped(
        self,
        *,
        worker_name: str,
        stopped_at: datetime,
        jobs_processed: int,
        last_error: str | None = None,
    ) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE worker_heartbeats
                    SET status = 'STOPPED',
                        last_heartbeat_at = ?,
                        current_job_id = NULL,
                        current_job_type = NULL,
                        jobs_processed = ?,
                        last_error = ?,
                        stopped_at = ?
                    WHERE worker_name = ?
                    """,
                    (
                        stopped_at.isoformat(),
                        jobs_processed,
                        last_error,
                        stopped_at.isoformat(),
                        worker_name,
                    ),
                )
        except sqlite3.Error as error:
            raise DataStoreError(
                "Worker stop state could not be saved.",
                code="WORKER_HEARTBEAT_STOP_FAILED",
            ) from error

    def get(
        self,
        *,
        worker_name: str,
    ) -> WorkerHeartbeat | None:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT *
                    FROM worker_heartbeats
                    WHERE worker_name = ?
                    """,
                    (worker_name,),
                ).fetchone()
        except sqlite3.Error as error:
            raise DataStoreError(
                "Worker heartbeat could not be loaded.",
                code="WORKER_HEARTBEAT_LOAD_FAILED",
            ) from error

        if row is None:
            return None

        return WorkerHeartbeat(
            worker_name=row["worker_name"],
            process_id=int(row["process_id"]),
            status=row["status"],
            started_at=datetime.fromisoformat(
                row["started_at"]
            ),
            last_heartbeat_at=datetime.fromisoformat(
                row["last_heartbeat_at"]
            ),
            current_job_id=row["current_job_id"],
            current_job_type=row["current_job_type"],
            jobs_processed=int(row["jobs_processed"]),
            last_error=row["last_error"],
            stopped_at=(
                None
                if row["stopped_at"] is None
                else datetime.fromisoformat(
                    row["stopped_at"]
                )
            ),
        )

    def ping(self) -> bool:
        try:
            with self._connect() as connection:
                value = connection.execute(
                    "SELECT 1"
                ).fetchone()[0]
        except sqlite3.Error:
            return False
        return value == 1

    def _upsert(
        self,
        *,
        heartbeat: WorkerHeartbeat,
    ) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO worker_heartbeats (
                        worker_name,
                        process_id,
                        status,
                        started_at,
                        last_heartbeat_at,
                        current_job_id,
                        current_job_type,
                        jobs_processed,
                        last_error,
                        stopped_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(worker_name) DO UPDATE SET
                        process_id = excluded.process_id,
                        status = excluded.status,
                        started_at = excluded.started_at,
                        last_heartbeat_at = excluded.last_heartbeat_at,
                        current_job_id = excluded.current_job_id,
                        current_job_type = excluded.current_job_type,
                        jobs_processed = excluded.jobs_processed,
                        last_error = excluded.last_error,
                        stopped_at = excluded.stopped_at
                    """,
                    (
                        heartbeat.worker_name,
                        heartbeat.process_id,
                        heartbeat.status,
                        heartbeat.started_at.isoformat(),
                        heartbeat.last_heartbeat_at.isoformat(),
                        heartbeat.current_job_id,
                        heartbeat.current_job_type,
                        heartbeat.jobs_processed,
                        heartbeat.last_error,
                        (
                            None
                            if heartbeat.stopped_at is None
                            else heartbeat.stopped_at.isoformat()
                        ),
                    ),
                )
        except sqlite3.Error as error:
            raise DataStoreError(
                "Worker heartbeat could not be saved.",
                code="WORKER_HEARTBEAT_SAVE_FAILED",
            ) from error

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._database_path,
            timeout=10.0,
        )
        connection.row_factory = sqlite3.Row
        return connection
