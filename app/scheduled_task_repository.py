import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.application_errors import DataStoreError
from app.job import JobType
from app.scheduled_task import CatchUpPolicy, ScheduledTask, ScheduleKind


class ScheduledTaskRepository:
    def __init__(self, *, database_path: str) -> None:
        cleaned = database_path.strip()
        if not cleaned:
            raise ValueError("Schedule database path is required.")
        self._database_path = Path(cleaned)

    def initialize(self) -> None:
        try:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS scheduled_tasks (
                        schedule_id TEXT PRIMARY KEY,
                        task_type TEXT NOT NULL,
                        enabled INTEGER NOT NULL,
                        schedule_kind TEXT NOT NULL,
                        timezone_name TEXT NOT NULL,
                        interval_seconds INTEGER,
                        local_hour INTEGER,
                        local_minute INTEGER,
                        weekday INTEGER,
                        next_run_at TEXT NOT NULL,
                        last_run_at TEXT,
                        last_job_id TEXT,
                        last_status TEXT,
                        payload_json TEXT NOT NULL,
                        catch_up_policy TEXT NOT NULL,
                        catch_up_window_seconds INTEGER,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        claim_token TEXT,
                        claimed_until TEXT
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_due
                    ON scheduled_tasks(enabled, next_run_at)
                    """
                )
        except sqlite3.Error as error:
            raise DataStoreError(
                "Schedule database could not be initialized.",
                code="SCHEDULE_DATABASE_INITIALIZE_FAILED",
            ) from error

    def add(self, *, task: ScheduledTask) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO scheduled_tasks (
                        schedule_id, task_type, enabled, schedule_kind,
                        timezone_name, interval_seconds, local_hour,
                        local_minute, weekday, next_run_at, last_run_at,
                        last_job_id, last_status, payload_json,
                        catch_up_policy, catch_up_window_seconds,
                        created_at, updated_at, claim_token, claimed_until
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    self._values(task),
                )
        except sqlite3.IntegrityError as error:
            raise DataStoreError(
                "Schedule already exists.",
                code="SCHEDULE_DUPLICATE",
                context={"schedule_id": task.schedule_id},
            ) from error
        except sqlite3.Error as error:
            raise DataStoreError(
                "Schedule could not be saved.",
                code="SCHEDULE_SAVE_FAILED",
            ) from error

    def get(self, *, schedule_id: str) -> ScheduledTask | None:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT * FROM scheduled_tasks WHERE schedule_id = ?",
                    (schedule_id,),
                ).fetchone()
        except sqlite3.Error as error:
            raise DataStoreError(
                "Schedule could not be loaded.",
                code="SCHEDULE_LOAD_FAILED",
            ) from error
        return None if row is None else self._row_to_task(row)

    def list_all(self) -> tuple[ScheduledTask, ...]:
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    "SELECT * FROM scheduled_tasks ORDER BY next_run_at, schedule_id"
                ).fetchall()
        except sqlite3.Error as error:
            raise DataStoreError(
                "Schedules could not be listed.",
                code="SCHEDULE_LIST_FAILED",
            ) from error
        return tuple(self._row_to_task(row) for row in rows)


    def update(self, *, task: ScheduledTask) -> bool:
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    UPDATE scheduled_tasks
                    SET task_type = ?, enabled = ?, schedule_kind = ?,
                        timezone_name = ?, interval_seconds = ?, local_hour = ?,
                        local_minute = ?, weekday = ?, next_run_at = ?,
                        last_run_at = ?, last_job_id = ?, last_status = ?,
                        payload_json = ?, catch_up_policy = ?,
                        catch_up_window_seconds = ?, updated_at = ?,
                        claim_token = NULL, claimed_until = NULL
                    WHERE schedule_id = ?
                    """,
                    (
                        task.task_type.value, int(task.enabled),
                        task.schedule_kind.value, task.timezone_name,
                        task.interval_seconds, task.local_hour,
                        task.local_minute, task.weekday,
                        task.next_run_at.isoformat(), _iso(task.last_run_at),
                        task.last_job_id, task.last_status, task.payload_json(),
                        task.catch_up_policy.value,
                        task.catch_up_window_seconds,
                        (_iso(task.updated_at) or task.next_run_at.isoformat()),
                        task.schedule_id,
                    ),
                )
                return cursor.rowcount == 1
        except sqlite3.Error as error:
            raise DataStoreError(
                "Schedule could not be updated.",
                code="SCHEDULE_UPDATE_FAILED",
            ) from error

    def set_enabled(
        self, *, schedule_id: str, enabled: bool, updated_at: datetime
    ) -> bool:
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    UPDATE scheduled_tasks
                    SET enabled = ?, updated_at = ?, claim_token = NULL,
                        claimed_until = NULL
                    WHERE schedule_id = ?
                    """,
                    (int(enabled), updated_at.isoformat(), schedule_id),
                )
                return cursor.rowcount == 1
        except sqlite3.Error as error:
            raise DataStoreError(
                "Schedule state could not be updated.",
                code="SCHEDULE_STATE_UPDATE_FAILED",
            ) from error

    def delete(self, *, schedule_id: str) -> bool:
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    "DELETE FROM scheduled_tasks WHERE schedule_id = ?",
                    (schedule_id,),
                )
                return cursor.rowcount == 1
        except sqlite3.Error as error:
            raise DataStoreError(
                "Schedule could not be deleted.",
                code="SCHEDULE_DELETE_FAILED",
            ) from error

    def claim_next_due(
        self,
        *,
        now: datetime,
        claimed_until: datetime,
        claim_token: str,
    ) -> ScheduledTask | None:
        if now.tzinfo is None or claimed_until.tzinfo is None:
            raise ValueError("Schedule claim times must be timezone-aware.")
        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    """
                    SELECT * FROM scheduled_tasks
                    WHERE enabled = 1
                      AND next_run_at <= ?
                      AND (claimed_until IS NULL OR claimed_until < ?)
                    ORDER BY next_run_at, schedule_id
                    LIMIT 1
                    """,
                    (now.isoformat(), now.isoformat()),
                ).fetchone()
                if row is None:
                    connection.commit()
                    return None
                cursor = connection.execute(
                    """
                    UPDATE scheduled_tasks
                    SET claim_token = ?, claimed_until = ?, updated_at = ?
                    WHERE schedule_id = ?
                      AND (claimed_until IS NULL OR claimed_until < ?)
                    """,
                    (
                        claim_token,
                        claimed_until.isoformat(),
                        now.isoformat(),
                        row["schedule_id"],
                        now.isoformat(),
                    ),
                )
                if cursor.rowcount != 1:
                    connection.rollback()
                    return None
                connection.commit()
            return self.get(schedule_id=row["schedule_id"])
        except sqlite3.Error as error:
            raise DataStoreError(
                "Due schedule could not be claimed.",
                code="SCHEDULE_CLAIM_FAILED",
            ) from error

    def complete_claim(
        self,
        *,
        schedule_id: str,
        claim_token: str,
        next_run_at: datetime,
        last_run_at: datetime,
        last_job_id: str | None,
        last_status: str,
        updated_at: datetime,
    ) -> bool:
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    UPDATE scheduled_tasks
                    SET next_run_at = ?, last_run_at = ?, last_job_id = ?,
                        last_status = ?, updated_at = ?, claim_token = NULL,
                        claimed_until = NULL
                    WHERE schedule_id = ? AND claim_token = ?
                    """,
                    (
                        next_run_at.isoformat(), last_run_at.isoformat(),
                        last_job_id, last_status, updated_at.isoformat(),
                        schedule_id, claim_token,
                    ),
                )
                return cursor.rowcount == 1
        except sqlite3.Error as error:
            raise DataStoreError(
                "Schedule claim could not be completed.",
                code="SCHEDULE_COMPLETE_FAILED",
            ) from error

    def release_claim(
        self,
        *,
        schedule_id: str,
        claim_token: str,
        last_status: str,
        updated_at: datetime,
    ) -> bool:
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    UPDATE scheduled_tasks
                    SET claim_token = NULL, claimed_until = NULL,
                        last_status = ?, updated_at = ?
                    WHERE schedule_id = ? AND claim_token = ?
                    """,
                    (last_status, updated_at.isoformat(), schedule_id, claim_token),
                )
                return cursor.rowcount == 1
        except sqlite3.Error as error:
            raise DataStoreError(
                "Schedule claim could not be released.",
                code="SCHEDULE_RELEASE_FAILED",
            ) from error

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=30.0)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _values(task: ScheduledTask) -> tuple[object, ...]:
        return (
            task.schedule_id, task.task_type.value, int(task.enabled),
            task.schedule_kind.value, task.timezone_name,
            task.interval_seconds, task.local_hour, task.local_minute,
            task.weekday, task.next_run_at.isoformat(),
            _iso(task.last_run_at), task.last_job_id, task.last_status,
            task.payload_json(), task.catch_up_policy.value,
            task.catch_up_window_seconds,
            _iso(task.created_at) or task.next_run_at.isoformat(),
            _iso(task.updated_at) or task.next_run_at.isoformat(),
            task.claim_token, _iso(task.claimed_until),
        )

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> ScheduledTask:
        try:
            return ScheduledTask(
                schedule_id=row["schedule_id"],
                task_type=JobType(row["task_type"]),
                enabled=bool(row["enabled"]),
                schedule_kind=ScheduleKind(row["schedule_kind"]),
                timezone_name=row["timezone_name"],
                interval_seconds=row["interval_seconds"],
                local_hour=row["local_hour"],
                local_minute=row["local_minute"],
                weekday=row["weekday"],
                next_run_at=datetime.fromisoformat(row["next_run_at"]),
                last_run_at=_datetime(row["last_run_at"]),
                last_job_id=row["last_job_id"],
                last_status=row["last_status"],
                payload=json.loads(row["payload_json"]),
                catch_up_policy=CatchUpPolicy(row["catch_up_policy"]),
                catch_up_window_seconds=row["catch_up_window_seconds"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                claim_token=row["claim_token"],
                claimed_until=_datetime(row["claimed_until"]),
            )
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            raise DataStoreError(
                "Stored schedule is invalid.",
                code="SCHEDULE_RECORD_INVALID",
            ) from error


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()


def _datetime(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value)