import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.symbol_decision_models import (
    SymbolDecisionStage,
    SymbolDecisionTrace,
)


class SymbolDecisionRepository:
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
                symbol_decision_traces (
                    trace_id TEXT PRIMARY KEY,
                    captured_at TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    rank INTEGER NOT NULL,
                    decision TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    score REAL NOT NULL,
                    confidence REAL NOT NULL,
                    headline TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    sentiment TEXT NOT NULL,
                    eligible_for_trade INTEGER NOT NULL,
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
                idx_symbol_decisions_symbol_time
                ON symbol_decision_traces(
                    symbol,
                    captured_at DESC
                )
                """
            )

    def save(
        self,
        *,
        trace: SymbolDecisionTrace,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO
                symbol_decision_traces (
                    trace_id,
                    captured_at,
                    symbol,
                    rank,
                    decision,
                    classification,
                    score,
                    confidence,
                    headline,
                    event_type,
                    sentiment,
                    eligible_for_trade,
                    trading_readiness,
                    graduation_ready,
                    summary,
                    stages_json,
                    blockers_json
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    trace.trace_id,
                    trace.captured_at.isoformat(),
                    trace.symbol,
                    trace.rank,
                    trace.decision,
                    trace.classification,
                    trace.score,
                    trace.confidence,
                    trace.headline,
                    trace.event_type,
                    trace.sentiment,
                    int(
                        trace.eligible_for_trade
                    ),
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

    def latest_for_symbol(
        self,
        *,
        symbol: str,
    ) -> SymbolDecisionTrace | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM symbol_decision_traces
                WHERE symbol = ?
                ORDER BY captured_at DESC
                LIMIT 1
                """,
                (symbol.upper().strip(),),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_trace(row)

    def list_recent(
        self,
        *,
        limit: int = 100,
        symbol: str | None = None,
    ) -> tuple[
        SymbolDecisionTrace,
        ...
    ]:
        if limit <= 0:
            return ()

        with self._connect() as connection:
            if symbol is None:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM symbol_decision_traces
                    ORDER BY captured_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM symbol_decision_traces
                    WHERE symbol = ?
                    ORDER BY captured_at DESC
                    LIMIT ?
                    """,
                    (
                        symbol.upper().strip(),
                        limit,
                    ),
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
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _row_to_trace(
        row: sqlite3.Row,
    ) -> SymbolDecisionTrace:
        stage_payload = json.loads(
            str(row["stages_json"])
        )

        return SymbolDecisionTrace(
            trace_id=str(row["trace_id"]),
            captured_at=(
                datetime.fromisoformat(
                    str(row["captured_at"])
                )
            ),
            symbol=str(row["symbol"]),
            rank=int(row["rank"]),
            decision=str(row["decision"]),
            classification=str(
                row["classification"]
            ),
            score=float(row["score"]),
            confidence=float(
                row["confidence"]
            ),
            headline=str(row["headline"]),
            event_type=str(
                row["event_type"]
            ),
            sentiment=str(row["sentiment"]),
            eligible_for_trade=bool(
                row["eligible_for_trade"]
            ),
            trading_readiness=str(
                row["trading_readiness"]
            ),
            graduation_ready=bool(
                row["graduation_ready"]
            ),
            summary=str(row["summary"]),
            stages=tuple(
                SymbolDecisionStage(
                    sequence=int(
                        item["sequence"]
                    ),
                    stage=str(item["stage"]),
                    status=str(item["status"]),
                    title=str(item["title"]),
                    summary=str(item["summary"]),
                    evidence=tuple(
                        str(value)
                        for value
                        in item.get(
                            "evidence",
                            (),
                        )
                    ),
                )
                for item in stage_payload
            ),
            blockers=tuple(
                json.loads(
                    str(row["blockers_json"])
                )
            ),
        )
