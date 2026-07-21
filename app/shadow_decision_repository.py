import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.application_errors import DataStoreError
from app.shadow_decision import ShadowAction, ShadowDecision


class ShadowDecisionRepository:
    def __init__(self, *, database_path: str) -> None:
        if not database_path.strip():
            raise ValueError(
                "Shadow-decision database path is required."
            )
        self._database_path = Path(database_path)

    def initialize(self) -> None:
        try:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS shadow_decisions (
                        decision_id TEXT PRIMARY KEY,
                        article_id TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        model_version TEXT NOT NULL,
                        action TEXT NOT NULL,
                        score REAL NOT NULL,
                        confidence REAL NOT NULL,
                        sentiment TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        is_material INTEGER NOT NULL,
                        headline TEXT NOT NULL,
                        eligible_for_trade INTEGER NOT NULL,
                        reasons_json TEXT NOT NULL,
                        blocking_reasons_json TEXT NOT NULL,
                        reference_price REAL,
                        reference_captured_at TEXT,
                        UNIQUE(article_id, model_version)
                    );

                    CREATE INDEX IF NOT EXISTS
                    idx_shadow_decisions_created_at
                    ON shadow_decisions(created_at DESC);

                    CREATE INDEX IF NOT EXISTS
                    idx_shadow_decisions_symbol
                    ON shadow_decisions(symbol, created_at DESC);
                    """
                )
        except sqlite3.Error as error:
            raise DataStoreError(
                "Shadow-decision storage could not be initialized.",
                code="SHADOW_STORAGE_INITIALIZE_FAILED",
            ) from error

    def add_if_missing(self, *, decision: ShadowDecision) -> bool:
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO shadow_decisions (
                        decision_id, article_id, symbol, created_at,
                        model_version, action, score, confidence,
                        sentiment, event_type, is_material, headline,
                        eligible_for_trade, reasons_json,
                        blocking_reasons_json, reference_price,
                        reference_captured_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    self._values(decision),
                )
                return cursor.rowcount == 1
        except sqlite3.Error as error:
            raise DataStoreError(
                "Shadow decision could not be saved.",
                code="SHADOW_DECISION_SAVE_FAILED",
            ) from error

    def list_recent(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        symbol: str | None = None,
        action: ShadowAction | None = None,
    ) -> tuple[ShadowDecision, ...]:
        if limit <= 0 or offset < 0:
            raise ValueError(
                "Shadow-decision pagination is invalid."
            )

        clauses: list[str] = []
        parameters: list[object] = []
        if symbol:
            clauses.append("symbol = ?")
            parameters.append(symbol.upper().strip())
        if action is not None:
            clauses.append("action = ?")
            parameters.append(action.value)

        sql = "SELECT * FROM shadow_decisions"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        parameters.extend((limit, offset))

        try:
            with self._connect() as connection:
                rows = connection.execute(sql, parameters).fetchall()
        except sqlite3.Error as error:
            raise DataStoreError(
                "Shadow decisions could not be loaded.",
                code="SHADOW_DECISION_LOAD_FAILED",
            ) from error

        return tuple(self._row_to_decision(row) for row in rows)

    def count(self) -> int:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT COUNT(*) AS count FROM shadow_decisions"
                ).fetchone()
        except sqlite3.Error as error:
            raise DataStoreError(
                "Shadow decisions could not be counted.",
                code="SHADOW_DECISION_COUNT_FAILED",
            ) from error
        return int(row["count"])

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _values(decision: ShadowDecision) -> tuple[object, ...]:
        return (
            decision.decision_id,
            decision.article_id,
            decision.symbol,
            decision.created_at.isoformat(),
            decision.model_version,
            decision.action.value,
            decision.score,
            decision.confidence,
            decision.sentiment,
            decision.event_type,
            int(decision.is_material),
            decision.headline,
            int(decision.eligible_for_trade),
            json.dumps(list(decision.reasons)),
            json.dumps(list(decision.blocking_reasons)),
            decision.reference_price,
            None
            if decision.reference_captured_at is None
            else decision.reference_captured_at.isoformat(),
        )

    @staticmethod
    def _row_to_decision(row: sqlite3.Row) -> ShadowDecision:
        return ShadowDecision(
            decision_id=row["decision_id"],
            article_id=row["article_id"],
            symbol=row["symbol"],
            created_at=datetime.fromisoformat(row["created_at"]),
            model_version=row["model_version"],
            action=ShadowAction(row["action"]),
            score=float(row["score"]),
            confidence=float(row["confidence"]),
            sentiment=row["sentiment"],
            event_type=row["event_type"],
            is_material=bool(row["is_material"]),
            headline=row["headline"],
            eligible_for_trade=bool(row["eligible_for_trade"]),
            reasons=tuple(json.loads(row["reasons_json"])),
            blocking_reasons=tuple(
                json.loads(row["blocking_reasons_json"])
            ),
            reference_price=(
                None
                if row["reference_price"] is None
                else float(row["reference_price"])
            ),
            reference_captured_at=(
                None
                if row["reference_captured_at"] is None
                else datetime.fromisoformat(
                    row["reference_captured_at"]
                )
            ),
        )
