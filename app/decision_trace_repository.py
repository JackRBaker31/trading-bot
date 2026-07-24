import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.decision_trace_models import (
    DecisionTrace,
    DecisionTraceStage,
)


class DecisionTraceRepository:
    def __init__(
        self,
        *,
        database_path: str,
    ) -> None:
        self._database_path = (
            database_path
        )

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
                decision_traces (
                    trace_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    symbol TEXT,
                    decision TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    trading_readiness TEXT NOT NULL,
                    graduation_ready INTEGER NOT NULL,
                    summary TEXT NOT NULL,
                    stages_json TEXT NOT NULL,
                    blockers_json TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_decision_traces_created_at
                ON decision_traces(
                    created_at DESC
                )
                """
            )

    def save(
        self,
        *,
        trace: DecisionTrace,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO
                decision_traces (
                    trace_id,
                    created_at,
                    symbol,
                    decision,
                    confidence,
                    trading_readiness,
                    graduation_ready,
                    summary,
                    stages_json,
                    blockers_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace.trace_id,
                    trace.created_at.isoformat(),
                    trace.symbol,
                    trace.decision,
                    trace.confidence,
                    trace.trading_readiness,
                    int(
                        trace.graduation_ready
                    ),
                    trace.summary,
                    json.dumps(
                        [
                            stage.to_dictionary()
                            for stage
                            in trace.stages
                        ]
                    ),
                    json.dumps(
                        list(trace.blockers)
                    ),
                ),
            )

    def latest(
        self,
    ) -> DecisionTrace | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM decision_traces
                ORDER BY created_at DESC
                LIMIT 1
                """
            ).fetchone()

        if row is None:
            return None

        return self._row_to_trace(
            row
        )

    def list_recent(
        self,
        *,
        limit: int = 50,
    ) -> tuple[
        DecisionTrace,
        ...
    ]:
        if limit <= 0:
            return ()

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM decision_traces
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return tuple(
            self._row_to_trace(row)
            for row in rows
        )

    def _connect(
        self,
    ) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._database_path
        )
        connection.row_factory = (
            sqlite3.Row
        )
        return connection

    @staticmethod
    def _row_to_trace(
        row: sqlite3.Row,
    ) -> DecisionTrace:
        stages_payload = json.loads(
            str(row["stages_json"])
        )

        return DecisionTrace(
            trace_id=str(
                row["trace_id"]
            ),
            created_at=(
                datetime.fromisoformat(
                    str(
                        row[
                            "created_at"
                        ]
                    )
                )
            ),
            symbol=(
                None
                if row["symbol"] is None
                else str(row["symbol"])
            ),
            decision=str(
                row["decision"]
            ),
            confidence=float(
                row["confidence"]
            ),
            trading_readiness=str(
                row[
                    "trading_readiness"
                ]
            ),
            graduation_ready=bool(
                row[
                    "graduation_ready"
                ]
            ),
            summary=str(
                row["summary"]
            ),
            stages=tuple(
                DecisionTraceStage(
                    sequence=int(
                        item["sequence"]
                    ),
                    stage=str(
                        item["stage"]
                    ),
                    status=str(
                        item["status"]
                    ),
                    title=str(
                        item["title"]
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
                )
                for item
                in stages_payload
            ),
            blockers=tuple(
                json.loads(
                    str(
                        row[
                            "blockers_json"
                        ]
                    )
                )
            ),
        )
