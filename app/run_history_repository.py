import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.application_errors import (
    DataStoreError,
)
from app.run_history import (
    RunHistoryRecord,
    RunStatus,
    RunType,
)


class RunHistoryRepository:
    def __init__(
        self,
        *,
        database_path: str,
    ) -> None:
        cleaned_path = database_path.strip()

        if not cleaned_path:
            raise ValueError(
                "Run-history database path is required."
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
                    CREATE TABLE IF NOT EXISTS run_history (
                        run_id TEXT PRIMARY KEY,
                        run_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        started_at TEXT NOT NULL,
                        finished_at TEXT,
                        provider TEXT,
                        symbols_json TEXT NOT NULL,
                        created_count INTEGER NOT NULL,
                        skipped_count INTEGER NOT NULL,
                        failure_count INTEGER NOT NULL,
                        error_code TEXT,
                        error_summary TEXT,
                        metadata_json TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_run_history_started_at
                    ON run_history(started_at DESC)
                    """
                )
        except sqlite3.Error as error:
            raise DataStoreError(
                "Run-history database could not "
                "be initialized.",
                code="RUN_HISTORY_INITIALIZE_FAILED",
                context={
                    "database_path": str(
                        self._database_path
                    )
                },
            ) from error

    def add(
        self,
        *,
        record: RunHistoryRecord,
    ) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO run_history (
                        run_id,
                        run_type,
                        status,
                        started_at,
                        finished_at,
                        provider,
                        symbols_json,
                        created_count,
                        skipped_count,
                        failure_count,
                        error_code,
                        error_summary,
                        metadata_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    self._record_values(record),
                )
        except sqlite3.IntegrityError as error:
            raise DataStoreError(
                "Run-history record already exists.",
                code="RUN_HISTORY_DUPLICATE",
                context={"run_id": record.run_id},
            ) from error
        except sqlite3.Error as error:
            raise DataStoreError(
                "Run-history record could not be saved.",
                code="RUN_HISTORY_SAVE_FAILED",
                context={"run_id": record.run_id},
            ) from error

    def update(
        self,
        *,
        record: RunHistoryRecord,
    ) -> None:
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    UPDATE run_history
                    SET
                        run_type = ?,
                        status = ?,
                        started_at = ?,
                        finished_at = ?,
                        provider = ?,
                        symbols_json = ?,
                        created_count = ?,
                        skipped_count = ?,
                        failure_count = ?,
                        error_code = ?,
                        error_summary = ?,
                        metadata_json = ?
                    WHERE run_id = ?
                    """,
                    (
                        record.run_type.value,
                        record.status.value,
                        record.started_at.isoformat(),
                        (
                            None
                            if record.finished_at is None
                            else record.finished_at.isoformat()
                        ),
                        record.provider,
                        json.dumps(
                            list(record.symbols)
                        ),
                        record.created_count,
                        record.skipped_count,
                        record.failure_count,
                        record.error_code,
                        record.error_summary,
                        record.metadata_json(),
                        record.run_id,
                    ),
                )

                if cursor.rowcount != 1:
                    raise DataStoreError(
                        "Run-history record was not found.",
                        code="RUN_HISTORY_NOT_FOUND",
                        context={"run_id": record.run_id},
                    )
        except DataStoreError:
            raise
        except sqlite3.Error as error:
            raise DataStoreError(
                "Run-history record could not be updated.",
                code="RUN_HISTORY_UPDATE_FAILED",
                context={"run_id": record.run_id},
            ) from error

    def get(
        self,
        *,
        run_id: str,
    ) -> RunHistoryRecord | None:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT *
                    FROM run_history
                    WHERE run_id = ?
                    """,
                    (run_id,),
                ).fetchone()
        except sqlite3.Error as error:
            raise DataStoreError(
                "Run-history record could not be loaded.",
                code="RUN_HISTORY_LOAD_FAILED",
                context={"run_id": run_id},
            ) from error

        if row is None:
            return None

        return self._row_to_record(row)

    def list_recent(
        self,
        *,
        limit: int = 50,
        run_type: RunType | None = None,
    ) -> tuple[RunHistoryRecord, ...]:
        if limit <= 0:
            raise ValueError(
                "Run-history limit must be positive."
            )

        sql = """
            SELECT *
            FROM run_history
        """
        parameters: tuple[object, ...] = ()

        if run_type is not None:
            sql += " WHERE run_type = ?"
            parameters = (run_type.value,)

        sql += " ORDER BY started_at DESC LIMIT ?"
        parameters += (limit,)

        try:
            with self._connect() as connection:
                rows = connection.execute(
                    sql,
                    parameters,
                ).fetchall()
        except sqlite3.Error as error:
            raise DataStoreError(
                "Run-history records could not be listed.",
                code="RUN_HISTORY_LIST_FAILED",
            ) from error

        return tuple(
            self._row_to_record(row)
            for row in rows
        )

    def _connect(
        self,
    ) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._database_path
        )
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _record_values(
        record: RunHistoryRecord,
    ) -> tuple[object, ...]:
        return (
            record.run_id,
            record.run_type.value,
            record.status.value,
            record.started_at.isoformat(),
            (
                None
                if record.finished_at is None
                else record.finished_at.isoformat()
            ),
            record.provider,
            json.dumps(
                list(record.symbols)
            ),
            record.created_count,
            record.skipped_count,
            record.failure_count,
            record.error_code,
            record.error_summary,
            record.metadata_json(),
        )

    @staticmethod
    def _row_to_record(
        row: sqlite3.Row,
    ) -> RunHistoryRecord:
        try:
            return RunHistoryRecord(
                run_id=row["run_id"],
                run_type=RunType(
                    row["run_type"]
                ),
                status=RunStatus(
                    row["status"]
                ),
                started_at=datetime.fromisoformat(
                    row["started_at"]
                ),
                finished_at=(
                    None
                    if row["finished_at"] is None
                    else datetime.fromisoformat(
                        row["finished_at"]
                    )
                ),
                provider=row["provider"],
                symbols=tuple(
                    json.loads(
                        row["symbols_json"]
                    )
                ),
                created_count=row["created_count"],
                skipped_count=row["skipped_count"],
                failure_count=row["failure_count"],
                error_code=row["error_code"],
                error_summary=row["error_summary"],
                metadata=json.loads(
                    row["metadata_json"]
                ),
            )
        except (
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            raise DataStoreError(
                "Run-history record is invalid.",
                code="RUN_HISTORY_RECORD_INVALID",
            ) from error