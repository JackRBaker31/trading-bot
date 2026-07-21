import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.application_errors import (
    DataStoreError,
)
from app.job import (
    JobRecord,
    JobStatus,
    JobType,
)


class JobRepository:
    def __init__(
        self,
        *,
        database_path: str,
    ) -> None:
        cleaned_path = database_path.strip()

        if not cleaned_path:
            raise ValueError(
                "Job database path is required."
            )

        self._database_path = Path(
            cleaned_path
        )

    def initialize(self) -> None:
        try:
            self._database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with self._connect() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS jobs (
                        job_id TEXT PRIMARY KEY,
                        job_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        started_at TEXT,
                        finished_at TEXT,
                        payload_json TEXT NOT NULL,
                        result_json TEXT NOT NULL,
                        error_code TEXT,
                        error_summary TEXT,
                        idempotency_key TEXT
                    )
                    """
                )
                columns = {
                    row["name"]
                    for row in connection.execute(
                        "PRAGMA table_info(jobs)"
                    ).fetchall()
                }
                if "idempotency_key" not in columns:
                    connection.execute(
                        "ALTER TABLE jobs ADD COLUMN idempotency_key TEXT"
                    )
                connection.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS
                    idx_jobs_idempotency_key
                    ON jobs(idempotency_key)
                    WHERE idempotency_key IS NOT NULL
                    """
                )
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_jobs_status_created_at
                    ON jobs(status, created_at)
                    """
                )
        except sqlite3.Error as error:
            raise DataStoreError(
                "Job database could not be initialized.",
                code="JOB_DATABASE_INITIALIZE_FAILED",
            ) from error

    def add(
        self,
        *,
        record: JobRecord,
    ) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO jobs (
                        job_id,
                        job_type,
                        status,
                        created_at,
                        started_at,
                        finished_at,
                        payload_json,
                        result_json,
                        error_code,
                        error_summary,
                        idempotency_key
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    self._record_values(record),
                )
        except sqlite3.IntegrityError as error:
            raise DataStoreError(
                "Job already exists.",
                code="JOB_DUPLICATE",
                context={"job_id": record.job_id},
            ) from error
        except sqlite3.Error as error:
            raise DataStoreError(
                "Job could not be saved.",
                code="JOB_SAVE_FAILED",
                context={"job_id": record.job_id},
            ) from error

    def update(
        self,
        *,
        record: JobRecord,
    ) -> None:
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    UPDATE jobs
                    SET
                        job_type = ?,
                        status = ?,
                        created_at = ?,
                        started_at = ?,
                        finished_at = ?,
                        payload_json = ?,
                        result_json = ?,
                        error_code = ?,
                        error_summary = ?,
                        idempotency_key = ?
                    WHERE job_id = ?
                    """,
                    (
                        record.job_type.value,
                        record.status.value,
                        record.created_at.isoformat(),
                        self._iso_or_none(
                            record.started_at
                        ),
                        self._iso_or_none(
                            record.finished_at
                        ),
                        record.payload_json(),
                        record.result_json(),
                        record.error_code,
                        record.error_summary,
                        record.idempotency_key,
                        record.job_id,
                    ),
                )

                if cursor.rowcount != 1:
                    raise DataStoreError(
                        "Job was not found.",
                        code="JOB_NOT_FOUND",
                        context={
                            "job_id": record.job_id
                        },
                    )
        except DataStoreError:
            raise
        except sqlite3.Error as error:
            raise DataStoreError(
                "Job could not be updated.",
                code="JOB_UPDATE_FAILED",
                context={"job_id": record.job_id},
            ) from error

    def get(
        self,
        *,
        job_id: str,
    ) -> JobRecord | None:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT *
                    FROM jobs
                    WHERE job_id = ?
                    """,
                    (job_id,),
                ).fetchone()
        except sqlite3.Error as error:
            raise DataStoreError(
                "Job could not be loaded.",
                code="JOB_LOAD_FAILED",
                context={"job_id": job_id},
            ) from error

        return (
            None
            if row is None
            else self._row_to_record(row)
        )

    def get_by_idempotency_key(
        self,
        *,
        idempotency_key: str,
    ) -> JobRecord | None:
        cleaned = idempotency_key.strip()
        if not cleaned:
            raise ValueError("Idempotency key is required.")

        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT * FROM jobs WHERE idempotency_key = ?",
                    (cleaned,),
                ).fetchone()
        except sqlite3.Error as error:
            raise DataStoreError(
                "Job could not be loaded by idempotency key.",
                code="JOB_IDEMPOTENCY_LOAD_FAILED",
            ) from error

        return None if row is None else self._row_to_record(row)

    def list_recent(
        self,
        *,
        limit: int = 50,
        status: JobStatus | None = None,
        job_type: JobType | None = None,
    ) -> tuple[JobRecord, ...]:
        if limit <= 0:
            raise ValueError(
                "Job list limit must be positive."
            )

        clauses: list[str] = []
        parameters: list[object] = []

        if status is not None:
            clauses.append("status = ?")
            parameters.append(status.value)

        if job_type is not None:
            clauses.append("job_type = ?")
            parameters.append(job_type.value)

        sql = "SELECT * FROM jobs"

        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        sql += " ORDER BY created_at DESC LIMIT ?"
        parameters.append(limit)

        try:
            with self._connect() as connection:
                rows = connection.execute(
                    sql,
                    tuple(parameters),
                ).fetchall()
        except sqlite3.Error as error:
            raise DataStoreError(
                "Jobs could not be listed.",
                code="JOB_LIST_FAILED",
            ) from error

        return tuple(
            self._row_to_record(row)
            for row in rows
        )

    def claim_next_queued(
        self,
        *,
        started_at: datetime,
    ) -> JobRecord | None:
        if started_at.tzinfo is None:
            raise ValueError(
                "Job claim time must be timezone-aware."
            )

        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    """
                    SELECT *
                    FROM jobs
                    WHERE status = ?
                    ORDER BY created_at ASC
                    LIMIT 1
                    """,
                    (JobStatus.QUEUED.value,),
                ).fetchone()

                if row is None:
                    connection.commit()
                    return None

                cursor = connection.execute(
                    """
                    UPDATE jobs
                    SET status = ?, started_at = ?
                    WHERE job_id = ? AND status = ?
                    """,
                    (
                        JobStatus.RUNNING.value,
                        started_at.isoformat(),
                        row["job_id"],
                        JobStatus.QUEUED.value,
                    ),
                )

                if cursor.rowcount != 1:
                    connection.rollback()
                    return None

                connection.commit()

            claimed = self.get(
                job_id=row["job_id"]
            )
            return claimed
        except sqlite3.Error as error:
            raise DataStoreError(
                "Queued job could not be claimed.",
                code="JOB_CLAIM_FAILED",
            ) from error

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._database_path,
            timeout=30.0,
        )
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _record_values(
        record: JobRecord,
    ) -> tuple[object, ...]:
        return (
            record.job_id,
            record.job_type.value,
            record.status.value,
            record.created_at.isoformat(),
            JobRepository._iso_or_none(
                record.started_at
            ),
            JobRepository._iso_or_none(
                record.finished_at
            ),
            record.payload_json(),
            record.result_json(),
            record.error_code,
            record.error_summary,
            record.idempotency_key,
        )

    @staticmethod
    def _iso_or_none(
        value: datetime | None,
    ) -> str | None:
        return (
            None
            if value is None
            else value.isoformat()
        )

    @staticmethod
    def _row_to_record(
        row: sqlite3.Row,
    ) -> JobRecord:
        try:
            return JobRecord(
                job_id=row["job_id"],
                job_type=JobType(
                    row["job_type"]
                ),
                status=JobStatus(
                    row["status"]
                ),
                created_at=datetime.fromisoformat(
                    row["created_at"]
                ),
                started_at=(
                    None
                    if row["started_at"] is None
                    else datetime.fromisoformat(
                        row["started_at"]
                    )
                ),
                finished_at=(
                    None
                    if row["finished_at"] is None
                    else datetime.fromisoformat(
                        row["finished_at"]
                    )
                ),
                payload=json.loads(
                    row["payload_json"]
                ),
                result=json.loads(
                    row["result_json"]
                ),
                error_code=row["error_code"],
                error_summary=row["error_summary"],
                idempotency_key=(
                    row["idempotency_key"]
                    if "idempotency_key" in row.keys()
                    else None
                ),
            )
        except (
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            raise DataStoreError(
                "Stored job is invalid.",
                code="JOB_RECORD_INVALID",
            ) from error