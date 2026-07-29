from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.universe_governance_models import (
    UniverseCycleCoverage,
    UniverseVersion,
)


class UniverseGovernanceRepository:
    def __init__(self, *, database_path: str) -> None:
        self._database_path = database_path

    def initialize(self) -> None:
        Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS universe_versions (
                    version_id TEXT PRIMARY KEY,
                    checksum TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    symbol_count INTEGER NOT NULL,
                    groups_json TEXT NOT NULL,
                    symbols_json TEXT NOT NULL,
                    previous_version_id TEXT,
                    added_symbols_json TEXT NOT NULL,
                    removed_symbols_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_universe_versions_created
                ON universe_versions(created_at DESC)
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS universe_cycle_coverage (
                    coverage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    captured_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    version_id TEXT NOT NULL,
                    requested_count INTEGER NOT NULL,
                    processed_count INTEGER NOT NULL,
                    skipped_count INTEGER NOT NULL,
                    coverage_percent REAL NOT NULL,
                    processed_symbols_json TEXT NOT NULL,
                    skipped_symbols_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_universe_coverage_time
                ON universe_cycle_coverage(captured_at DESC)
                """
            )

    def get_by_checksum(self, *, checksum: str) -> UniverseVersion | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM universe_versions
                WHERE checksum = ?
                """,
                (checksum,),
            ).fetchone()
        return None if row is None else self._row_to_version(row)

    def latest_version(self) -> UniverseVersion | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM universe_versions
                ORDER BY created_at DESC, rowid DESC
                LIMIT 1
                """
            ).fetchone()
        return None if row is None else self._row_to_version(row)

    def add_version(self, *, version: UniverseVersion) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO universe_versions (
                    version_id,
                    checksum,
                    created_at,
                    source_path,
                    symbol_count,
                    groups_json,
                    symbols_json,
                    previous_version_id,
                    added_symbols_json,
                    removed_symbols_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version.version_id,
                    version.checksum,
                    version.created_at.astimezone(timezone.utc).isoformat(),
                    version.source_path,
                    version.symbol_count,
                    json.dumps(
                        {
                            key: list(values)
                            for key, values in version.groups.items()
                        },
                        sort_keys=True,
                    ),
                    json.dumps(list(version.symbols)),
                    version.previous_version_id,
                    json.dumps(list(version.added_symbols)),
                    json.dumps(list(version.removed_symbols)),
                ),
            )

    def list_versions(self, *, limit: int = 20) -> tuple[UniverseVersion, ...]:
        if limit <= 0:
            return ()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM universe_versions
                ORDER BY created_at DESC, rowid DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return tuple(self._row_to_version(row) for row in rows)

    def add_coverage(
        self,
        *,
        coverage: UniverseCycleCoverage,
    ) -> UniverseCycleCoverage:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO universe_cycle_coverage (
                    captured_at,
                    source,
                    version_id,
                    requested_count,
                    processed_count,
                    skipped_count,
                    coverage_percent,
                    processed_symbols_json,
                    skipped_symbols_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    coverage.captured_at.astimezone(timezone.utc).isoformat(),
                    coverage.source,
                    coverage.version_id,
                    coverage.requested_count,
                    coverage.processed_count,
                    coverage.skipped_count,
                    coverage.coverage_percent,
                    json.dumps(list(coverage.processed_symbols)),
                    json.dumps(list(coverage.skipped_symbols)),
                ),
            )
            coverage_id = int(cursor.lastrowid)
        return UniverseCycleCoverage(
            coverage_id=coverage_id,
            captured_at=coverage.captured_at,
            source=coverage.source,
            version_id=coverage.version_id,
            requested_count=coverage.requested_count,
            processed_count=coverage.processed_count,
            skipped_count=coverage.skipped_count,
            coverage_percent=coverage.coverage_percent,
            processed_symbols=coverage.processed_symbols,
            skipped_symbols=coverage.skipped_symbols,
        )

    def list_coverage(self, *, limit: int = 30) -> tuple[UniverseCycleCoverage, ...]:
        if limit <= 0:
            return ()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM universe_cycle_coverage
                ORDER BY captured_at DESC, coverage_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return tuple(self._row_to_coverage(row) for row in rows)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _row_to_version(row: sqlite3.Row) -> UniverseVersion:
        groups_payload = json.loads(str(row["groups_json"]))
        return UniverseVersion(
            version_id=str(row["version_id"]),
            checksum=str(row["checksum"]),
            created_at=datetime.fromisoformat(
                str(row["created_at"])
            ).astimezone(timezone.utc),
            source_path=str(row["source_path"]),
            symbol_count=int(row["symbol_count"]),
            groups={
                str(key): tuple(str(value) for value in values)
                for key, values in groups_payload.items()
            },
            symbols=tuple(
                str(value)
                for value in json.loads(str(row["symbols_json"]))
            ),
            previous_version_id=(
                None
                if row["previous_version_id"] is None
                else str(row["previous_version_id"])
            ),
            added_symbols=tuple(
                str(value)
                for value in json.loads(str(row["added_symbols_json"]))
            ),
            removed_symbols=tuple(
                str(value)
                for value in json.loads(str(row["removed_symbols_json"]))
            ),
        )

    @staticmethod
    def _row_to_coverage(row: sqlite3.Row) -> UniverseCycleCoverage:
        return UniverseCycleCoverage(
            coverage_id=int(row["coverage_id"]),
            captured_at=datetime.fromisoformat(
                str(row["captured_at"])
            ).astimezone(timezone.utc),
            source=str(row["source"]),
            version_id=str(row["version_id"]),
            requested_count=int(row["requested_count"]),
            processed_count=int(row["processed_count"]),
            skipped_count=int(row["skipped_count"]),
            coverage_percent=float(row["coverage_percent"]),
            processed_symbols=tuple(
                str(value)
                for value in json.loads(str(row["processed_symbols_json"]))
            ),
            skipped_symbols=tuple(
                str(value)
                for value in json.loads(str(row["skipped_symbols_json"]))
            ),
        )
