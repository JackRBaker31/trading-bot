import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.copilot_history_models import CopilotDecisionSnapshot


class CopilotHistoryRepository:
    def __init__(self, *, database_path: str) -> None:
        self._database_path = database_path

    def initialize(self) -> None:
        Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS copilot_decision_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    captured_at TEXT NOT NULL,
                    overall_status TEXT NOT NULL,
                    platform_status TEXT NOT NULL,
                    trading_readiness TEXT NOT NULL,
                    market_outlook TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    signal_count INTEGER NOT NULL,
                    actionable_signal_count INTEGER NOT NULL,
                    evidence_quality TEXT NOT NULL,
                    graduation_ready INTEGER NOT NULL,
                    graduation_passed_checks INTEGER NOT NULL,
                    graduation_total_checks INTEGER NOT NULL,
                    graduation_failed_checks INTEGER NOT NULL,
                    decision TEXT NOT NULL,
                    blockers_json TEXT NOT NULL
                )
            """)
            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_copilot_snapshots_captured_at
                ON copilot_decision_snapshots(captured_at DESC)
            """)

    def save(self, *, snapshot: CopilotDecisionSnapshot) -> None:
        with self._connect() as connection:
            connection.execute("""
                INSERT OR REPLACE INTO copilot_decision_snapshots
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.snapshot_id, snapshot.captured_at.isoformat(),
                snapshot.overall_status, snapshot.platform_status,
                snapshot.trading_readiness, snapshot.market_outlook,
                snapshot.confidence, snapshot.signal_count,
                snapshot.actionable_signal_count, snapshot.evidence_quality,
                int(snapshot.graduation_ready),
                snapshot.graduation_passed_checks,
                snapshot.graduation_total_checks,
                snapshot.graduation_failed_checks,
                snapshot.decision, json.dumps(list(snapshot.blockers)),
            ))

    def list_recent(self, *, limit: int = 100) -> tuple[CopilotDecisionSnapshot, ...]:
        if limit <= 0:
            return ()
        with self._connect() as connection:
            rows = connection.execute("""
                SELECT * FROM copilot_decision_snapshots
                ORDER BY captured_at DESC LIMIT ?
            """, (limit,)).fetchall()
        return tuple(self._row(row) for row in rows)

    def latest_before(self, *, captured_at: datetime) -> CopilotDecisionSnapshot | None:
        with self._connect() as connection:
            row = connection.execute("""
                SELECT * FROM copilot_decision_snapshots
                WHERE captured_at < ?
                ORDER BY captured_at DESC LIMIT 1
            """, (captured_at.isoformat(),)).fetchone()
        return None if row is None else self._row(row)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _row(row: sqlite3.Row) -> CopilotDecisionSnapshot:
        return CopilotDecisionSnapshot(
            snapshot_id=str(row["snapshot_id"]),
            captured_at=datetime.fromisoformat(str(row["captured_at"])),
            overall_status=str(row["overall_status"]),
            platform_status=str(row["platform_status"]),
            trading_readiness=str(row["trading_readiness"]),
            market_outlook=str(row["market_outlook"]),
            confidence=float(row["confidence"]),
            signal_count=int(row["signal_count"]),
            actionable_signal_count=int(row["actionable_signal_count"]),
            evidence_quality=str(row["evidence_quality"]),
            graduation_ready=bool(row["graduation_ready"]),
            graduation_passed_checks=int(row["graduation_passed_checks"]),
            graduation_total_checks=int(row["graduation_total_checks"]),
            graduation_failed_checks=int(row["graduation_failed_checks"]),
            decision=str(row["decision"]),
            blockers=tuple(json.loads(str(row["blockers_json"]))),
        )
