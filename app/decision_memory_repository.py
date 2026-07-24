import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.decision_memory_models import (
    DecisionMemoryCapability,
    DecisionMemoryRecord,
)


class DecisionMemoryRepository:
    def __init__(
        self,
        *,
        database_path: str,
    ) -> None:
        self._database_path = (
            database_path
        )

    def initialize(
        self,
    ) -> None:
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
                decision_memory (
                    decision_id TEXT PRIMARY KEY,
                    fingerprint TEXT NOT NULL UNIQUE,
                    captured_at TEXT NOT NULL,
                    thesis_generated_at TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    score REAL NOT NULL,
                    confidence REAL NOT NULL,
                    confidence_coverage REAL NOT NULL,
                    risk_tier TEXT NOT NULL,
                    time_horizon TEXT NOT NULL,
                    suggested_position_value REAL
                        NOT NULL,
                    eligible_for_execution INTEGER
                        NOT NULL,
                    headline TEXT NOT NULL,
                    primary_driver TEXT NOT NULL,
                    capabilities_json TEXT NOT NULL,
                    reasons_json TEXT NOT NULL,
                    blockers_json TEXT NOT NULL,
                    warnings_json TEXT NOT NULL,
                    executed INTEGER NOT NULL
                        DEFAULT 0,
                    paper_trade_id TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                ix_decision_memory_symbol_time
                ON decision_memory (
                    symbol,
                    captured_at DESC
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                ix_decision_memory_recommendation
                ON decision_memory (
                    recommendation,
                    captured_at DESC
                )
                """
            )
            connection.commit()

    def save_if_new(
        self,
        *,
        record: DecisionMemoryRecord,
    ) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO
                decision_memory (
                    decision_id,
                    fingerprint,
                    captured_at,
                    thesis_generated_at,
                    symbol,
                    recommendation,
                    score,
                    confidence,
                    confidence_coverage,
                    risk_tier,
                    time_horizon,
                    suggested_position_value,
                    eligible_for_execution,
                    headline,
                    primary_driver,
                    capabilities_json,
                    reasons_json,
                    blockers_json,
                    warnings_json,
                    executed,
                    paper_trade_id
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    record.decision_id,
                    record.fingerprint,
                    record.captured_at.isoformat(),
                    (
                        record
                        .thesis_generated_at
                        .isoformat()
                    ),
                    record.symbol,
                    record.recommendation,
                    record.score,
                    record.confidence,
                    (
                        record
                        .confidence_coverage
                    ),
                    record.risk_tier,
                    record.time_horizon,
                    (
                        record
                        .suggested_position_value
                    ),
                    int(
                        record
                        .eligible_for_execution
                    ),
                    record.headline,
                    record.primary_driver,
                    json.dumps(
                        [
                            item.to_dictionary()
                            for item
                            in record.capabilities
                        ],
                        separators=(
                            ",",
                            ":",
                        ),
                        sort_keys=True,
                    ),
                    json.dumps(
                        list(record.reasons),
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        list(record.blockers),
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        list(record.warnings),
                        separators=(",", ":"),
                    ),
                    int(record.executed),
                    record.paper_trade_id,
                ),
            )
            connection.commit()
            return cursor.rowcount == 1

    def list_recent(
        self,
        *,
        limit: int = 50,
        symbol: str | None = None,
        recommendation: (
            str | None
        ) = None,
    ) -> tuple[
        DecisionMemoryRecord,
        ...
    ]:
        if limit <= 0:
            raise ValueError(
                "Limit must be positive."
            )

        clauses: list[str] = []
        values: list[object] = []

        if symbol is not None:
            clauses.append(
                "symbol = ?"
            )
            values.append(
                symbol.upper().strip()
            )

        if recommendation is not None:
            clauses.append(
                "recommendation = ?"
            )
            values.append(
                recommendation
                .upper()
                .strip()
            )

        where = (
            " WHERE "
            + " AND ".join(clauses)
            if clauses
            else ""
        )

        values.append(limit)

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    decision_id,
                    fingerprint,
                    captured_at,
                    thesis_generated_at,
                    symbol,
                    recommendation,
                    score,
                    confidence,
                    confidence_coverage,
                    risk_tier,
                    time_horizon,
                    suggested_position_value,
                    eligible_for_execution,
                    headline,
                    primary_driver,
                    capabilities_json,
                    reasons_json,
                    blockers_json,
                    warnings_json,
                    executed,
                    paper_trade_id
                FROM decision_memory
                {where}
                ORDER BY captured_at DESC
                LIMIT ?
                """,
                tuple(values),
            ).fetchall()

        return tuple(
            self._from_row(row)
            for row in rows
        )

    def count_all(
        self,
    ) -> int:
        return self._count(
            """
            SELECT COUNT(*)
            FROM decision_memory
            """
        )

    def count_executable(
        self,
    ) -> int:
        return self._count(
            """
            SELECT COUNT(*)
            FROM decision_memory
            WHERE eligible_for_execution = 1
            """
        )

    def count_executed(
        self,
    ) -> int:
        return self._count(
            """
            SELECT COUNT(*)
            FROM decision_memory
            WHERE executed = 1
            """
        )

    def count_symbols(
        self,
    ) -> int:
        return self._count(
            """
            SELECT COUNT(
                DISTINCT symbol
            )
            FROM decision_memory
            """
        )

    def _count(
        self,
        query: str,
    ) -> int:
        with self._connect() as connection:
            row = connection.execute(
                query
            ).fetchone()

        return int(row[0])

    def _connect(
        self,
    ) -> sqlite3.Connection:
        return sqlite3.connect(
            self._database_path
        )

    @staticmethod
    def _from_row(
        row: tuple[object, ...],
    ) -> DecisionMemoryRecord:
        capabilities_payload = (
            json.loads(
                str(row[15])
            )
        )

        capabilities = tuple(
            DecisionMemoryCapability(
                capability=str(
                    item["capability"]
                ),
                status=str(
                    item["status"]
                ),
                score=(
                    float(item["score"])
                    if (
                        item.get("score")
                        is not None
                    )
                    else None
                ),
                maximum=float(
                    item["maximum"]
                ),
                confidence=(
                    float(
                        item["confidence"]
                    )
                    if (
                        item.get(
                            "confidence"
                        )
                        is not None
                    )
                    else None
                ),
                stance=str(
                    item["stance"]
                ),
                summary=str(
                    item["summary"]
                ),
                evidence=tuple(
                    str(value)
                    for value
                    in item.get(
                        "evidence",
                        (),
                    )
                ),
                blockers=tuple(
                    str(value)
                    for value
                    in item.get(
                        "blockers",
                        (),
                    )
                ),
            )
            for item
            in capabilities_payload
        )

        return DecisionMemoryRecord(
            decision_id=str(row[0]),
            fingerprint=str(row[1]),
            captured_at=(
                datetime.fromisoformat(
                    str(row[2])
                )
            ),
            thesis_generated_at=(
                datetime.fromisoformat(
                    str(row[3])
                )
            ),
            symbol=str(row[4]),
            recommendation=str(row[5]),
            score=float(row[6]),
            confidence=float(row[7]),
            confidence_coverage=float(
                row[8]
            ),
            risk_tier=str(row[9]),
            time_horizon=str(row[10]),
            suggested_position_value=float(
                row[11]
            ),
            eligible_for_execution=bool(
                row[12]
            ),
            headline=str(row[13]),
            primary_driver=str(row[14]),
            capabilities=capabilities,
            reasons=tuple(
                str(value)
                for value
                in json.loads(
                    str(row[16])
                )
            ),
            blockers=tuple(
                str(value)
                for value
                in json.loads(
                    str(row[17])
                )
            ),
            warnings=tuple(
                str(value)
                for value
                in json.loads(
                    str(row[18])
                )
            ),
            executed=bool(row[19]),
            paper_trade_id=(
                str(row[20])
                if row[20] is not None
                else None
            ),
        )
