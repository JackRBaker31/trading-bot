import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.opportunity_ranking_history_models import (
    OpportunityRankingCaptureResult,
    OpportunityRankingSnapshot,
)
from app.opportunity_ranking_models import OpportunityRankingReport, RankedOpportunity


class OpportunityRankingHistoryRepository:
    def __init__(
        self,
        *,
        database_path: str,
        minimum_score_change: float = 0.25,
        minimum_component_change: float = 0.25,
    ) -> None:
        if minimum_score_change < 0:
            raise ValueError("Minimum score change cannot be negative.")
        if minimum_component_change < 0:
            raise ValueError("Minimum component change cannot be negative.")
        self._database_path = database_path
        self._minimum_score_change = minimum_score_change
        self._minimum_component_change = minimum_component_change

    def initialize(self) -> None:
        Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS opportunity_ranking_snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    captured_at TEXT NOT NULL,
                    last_observed_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    methodology_version TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    rank INTEGER NOT NULL,
                    opportunity_score REAL NOT NULL,
                    category TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    calibrated_confidence REAL NOT NULL,
                    expected_return_percent REAL,
                    evidence_coverage_percent REAL NOT NULL,
                    data_quality TEXT NOT NULL,
                    risk_tier TEXT NOT NULL,
                    eligible_for_execution INTEGER NOT NULL,
                    historical_match_count INTEGER NOT NULL,
                    measured_case_count INTEGER NOT NULL,
                    sector TEXT NOT NULL,
                    headline TEXT NOT NULL,
                    component_values_json TEXT NOT NULL,
                    component_labels_json TEXT NOT NULL,
                    blockers_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_opportunity_history_symbol_time
                ON opportunity_ranking_snapshots(symbol, captured_at DESC)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_opportunity_history_time
                ON opportunity_ranking_snapshots(captured_at DESC)
                """
            )

    def record_report(
        self,
        *,
        report: OpportunityRankingReport,
        source: str = "REPORT",
    ) -> OpportunityRankingCaptureResult:
        source_clean = source.upper().strip() or "REPORT"
        observed = len(report.items)
        inserted = 0
        unchanged = 0

        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            for item in report.items:
                latest_row = connection.execute(
                    """
                    SELECT *
                    FROM opportunity_ranking_snapshots
                    WHERE symbol = ?
                    ORDER BY captured_at DESC, snapshot_id DESC
                    LIMIT 1
                    """,
                    (item.symbol,),
                ).fetchone()

                if latest_row is None or self._meaningfully_changed(
                    previous=self._row_to_snapshot(latest_row),
                    current=item,
                ):
                    self._insert(
                        connection=connection,
                        report=report,
                        item=item,
                        source=source_clean,
                    )
                    inserted += 1
                else:
                    connection.execute(
                        """
                        UPDATE opportunity_ranking_snapshots
                        SET last_observed_at = ?
                        WHERE snapshot_id = ?
                        """,
                        (
                            report.generated_at.astimezone(timezone.utc).isoformat(),
                            int(latest_row["snapshot_id"]),
                        ),
                    )
                    unchanged += 1
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

        return OpportunityRankingCaptureResult(
            observed_count=observed,
            inserted_count=inserted,
            unchanged_count=unchanged,
        )

    def list_for_symbol(
        self,
        *,
        symbol: str,
        limit: int = 1000,
    ) -> tuple[OpportunityRankingSnapshot, ...]:
        cleaned = symbol.upper().strip()
        if not cleaned or limit <= 0:
            return ()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM opportunity_ranking_snapshots
                WHERE symbol = ?
                ORDER BY captured_at ASC, snapshot_id ASC
                LIMIT ?
                """,
                (cleaned, limit),
            ).fetchall()
        return tuple(self._row_to_snapshot(row) for row in rows)

    def list_all(
        self,
        *,
        limit: int = 5000,
    ) -> tuple[OpportunityRankingSnapshot, ...]:
        if limit <= 0:
            return ()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM opportunity_ranking_snapshots
                ORDER BY captured_at ASC, snapshot_id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return tuple(self._row_to_snapshot(row) for row in rows)

    def _insert(
        self,
        *,
        connection: sqlite3.Connection,
        report: OpportunityRankingReport,
        item: RankedOpportunity,
        source: str,
    ) -> None:
        captured_at = report.generated_at.astimezone(timezone.utc).isoformat()
        component_values = {
            component.code: component.value for component in item.components
        }
        component_labels = {
            component.code: component.label for component in item.components
        }
        connection.execute(
            """
            INSERT INTO opportunity_ranking_snapshots (
                captured_at,
                last_observed_at,
                source,
                methodology_version,
                symbol,
                rank,
                opportunity_score,
                category,
                recommendation,
                calibrated_confidence,
                expected_return_percent,
                evidence_coverage_percent,
                data_quality,
                risk_tier,
                eligible_for_execution,
                historical_match_count,
                measured_case_count,
                sector,
                headline,
                component_values_json,
                component_labels_json,
                blockers_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                captured_at,
                captured_at,
                source,
                report.methodology_version,
                item.symbol,
                item.rank,
                item.opportunity_score,
                item.category,
                item.recommendation,
                item.calibrated_confidence,
                item.expected_return_percent,
                item.evidence_coverage_percent,
                item.data_quality,
                item.risk_tier,
                int(item.eligible_for_execution),
                item.historical_match_count,
                item.measured_case_count,
                item.sector,
                item.headline,
                json.dumps(component_values, sort_keys=True),
                json.dumps(component_labels, sort_keys=True),
                json.dumps(list(item.blockers), sort_keys=True),
            ),
        )

    def _meaningfully_changed(
        self,
        *,
        previous: OpportunityRankingSnapshot,
        current: RankedOpportunity,
    ) -> bool:
        if abs(current.opportunity_score - previous.opportunity_score) >= self._minimum_score_change:
            return True
        if current.rank != previous.rank:
            return True
        if current.eligible_for_execution != previous.eligible_for_execution:
            return True
        if current.category != previous.category:
            return True
        if tuple(current.blockers) != previous.blockers:
            return True

        current_components = {
            component.code: component.value for component in current.components
        }
        all_codes = set(previous.component_values) | set(current_components)
        return any(
            abs(current_components.get(code, 0.0) - previous.component_values.get(code, 0.0))
            >= self._minimum_component_change
            for code in all_codes
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _row_to_snapshot(row: sqlite3.Row) -> OpportunityRankingSnapshot:
        component_values_payload = json.loads(str(row["component_values_json"]))
        component_labels_payload = json.loads(str(row["component_labels_json"]))
        blockers_payload = json.loads(str(row["blockers_json"]))
        return OpportunityRankingSnapshot(
            snapshot_id=int(row["snapshot_id"]),
            captured_at=datetime.fromisoformat(str(row["captured_at"])).astimezone(timezone.utc),
            last_observed_at=datetime.fromisoformat(str(row["last_observed_at"])).astimezone(timezone.utc),
            source=str(row["source"]),
            methodology_version=str(row["methodology_version"]),
            symbol=str(row["symbol"]),
            rank=int(row["rank"]),
            opportunity_score=float(row["opportunity_score"]),
            category=str(row["category"]),
            recommendation=str(row["recommendation"]),
            calibrated_confidence=float(row["calibrated_confidence"]),
            expected_return_percent=(
                None
                if row["expected_return_percent"] is None
                else float(row["expected_return_percent"])
            ),
            evidence_coverage_percent=float(row["evidence_coverage_percent"]),
            data_quality=str(row["data_quality"]),
            risk_tier=str(row["risk_tier"]),
            eligible_for_execution=bool(row["eligible_for_execution"]),
            historical_match_count=int(row["historical_match_count"]),
            measured_case_count=int(row["measured_case_count"]),
            sector=str(row["sector"]),
            headline=str(row["headline"]),
            component_values={
                str(key): float(value)
                for key, value in component_values_payload.items()
            },
            component_labels={
                str(key): str(value)
                for key, value in component_labels_payload.items()
            },
            blockers=tuple(str(value) for value in blockers_payload),
        )
