import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.operation_diagnostics_models import (
    OperationDiagnosticEvent,
)


class OperationDiagnosticsRepository:
    def __init__(
        self,
        *,
        database_path: str,
    ) -> None:
        self._database_path = database_path

    def initialize(self) -> None:
        Path(
            self._database_path
        ).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS
                operation_diagnostics (
                    event_id TEXT PRIMARY KEY,
                    job_id TEXT,
                    stage TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    symbol TEXT,
                    provider TEXT,
                    error_code TEXT,
                    error_summary TEXT,
                    retryable INTEGER NOT NULL,
                    retry_count INTEGER NOT NULL,
                    recovered INTEGER NOT NULL,
                    latency_ms REAL,
                    cache_status TEXT,
                    context_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                ix_operation_diagnostics_job
                ON operation_diagnostics (
                    job_id,
                    occurred_at ASC
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                ix_operation_diagnostics_stage
                ON operation_diagnostics (
                    stage,
                    occurred_at DESC
                )
                """
            )
            connection.commit()

    def save(
        self,
        *,
        event: OperationDiagnosticEvent,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO
                operation_diagnostics (
                    event_id,
                    job_id,
                    stage,
                    operation,
                    occurred_at,
                    severity,
                    status,
                    symbol,
                    provider,
                    error_code,
                    error_summary,
                    retryable,
                    retry_count,
                    recovered,
                    latency_ms,
                    cache_status,
                    context_json
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    event.event_id,
                    event.job_id,
                    event.stage,
                    event.operation,
                    event.occurred_at.isoformat(),
                    event.severity,
                    event.status,
                    event.symbol,
                    event.provider,
                    event.error_code,
                    event.error_summary,
                    int(event.retryable),
                    event.retry_count,
                    int(event.recovered),
                    event.latency_ms,
                    event.cache_status,
                    json.dumps(
                        event.context,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ),
            )
            connection.commit()

    def list_for_job(
        self,
        *,
        job_id: str,
    ) -> tuple[
        OperationDiagnosticEvent,
        ...
    ]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    event_id,
                    job_id,
                    stage,
                    operation,
                    occurred_at,
                    severity,
                    status,
                    symbol,
                    provider,
                    error_code,
                    error_summary,
                    retryable,
                    retry_count,
                    recovered,
                    latency_ms,
                    cache_status,
                    context_json
                FROM operation_diagnostics
                WHERE job_id = ?
                ORDER BY occurred_at ASC
                """,
                (job_id,),
            ).fetchall()

        return tuple(
            self._from_row(row)
            for row in rows
        )

    def list_recent(
        self,
        *,
        limit: int = 100,
    ) -> tuple[
        OperationDiagnosticEvent,
        ...
    ]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    event_id,
                    job_id,
                    stage,
                    operation,
                    occurred_at,
                    severity,
                    status,
                    symbol,
                    provider,
                    error_code,
                    error_summary,
                    retryable,
                    retry_count,
                    recovered,
                    latency_ms,
                    cache_status,
                    context_json
                FROM operation_diagnostics
                ORDER BY occurred_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return tuple(
            self._from_row(row)
            for row in rows
        )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(
            self._database_path
        )

    @staticmethod
    def _from_row(
        row: tuple[object, ...],
    ) -> OperationDiagnosticEvent:
        return OperationDiagnosticEvent(
            event_id=str(row[0]),
            job_id=(
                str(row[1])
                if row[1] is not None
                else None
            ),
            stage=str(row[2]),
            operation=str(row[3]),
            occurred_at=(
                datetime.fromisoformat(
                    str(row[4])
                )
            ),
            severity=str(row[5]),
            status=str(row[6]),
            symbol=(
                str(row[7])
                if row[7] is not None
                else None
            ),
            provider=(
                str(row[8])
                if row[8] is not None
                else None
            ),
            error_code=(
                str(row[9])
                if row[9] is not None
                else None
            ),
            error_summary=(
                str(row[10])
                if row[10] is not None
                else None
            ),
            retryable=bool(row[11]),
            retry_count=int(row[12]),
            recovered=bool(row[13]),
            latency_ms=(
                float(row[14])
                if row[14] is not None
                else None
            ),
            cache_status=(
                str(row[15])
                if row[15] is not None
                else None
            ),
            context=dict(
                json.loads(
                    str(row[16])
                )
            ),
        )
