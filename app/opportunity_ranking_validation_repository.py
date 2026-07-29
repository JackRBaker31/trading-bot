import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from app.opportunity_ranking_validation_models import OpportunityForwardOutcome


class OpportunityRankingValidationRepository:
    def __init__(self, *, database_path: str) -> None:
        self._database_path = database_path

    def initialize(self) -> None:
        Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS opportunity_ranking_forward_outcomes (
                    outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL,
                    captured_at TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    horizon_days INTEGER NOT NULL,
                    entry_date TEXT NOT NULL,
                    exit_date TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    observed_price REAL NOT NULL,
                    return_percent REAL NOT NULL,
                    benchmark_symbol TEXT NOT NULL,
                    benchmark_entry_price REAL NOT NULL,
                    benchmark_observed_price REAL NOT NULL,
                    benchmark_return_percent REAL NOT NULL,
                    alpha_percent REAL NOT NULL,
                    maximum_favourable_excursion_percent REAL NOT NULL,
                    maximum_drawdown_percent REAL NOT NULL,
                    status TEXT NOT NULL,
                    original_rank INTEGER NOT NULL,
                    opportunity_score REAL NOT NULL,
                    calibrated_confidence REAL NOT NULL,
                    expected_return_percent REAL,
                    evidence_coverage_percent REAL NOT NULL,
                    eligible_for_execution INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    sector TEXT NOT NULL,
                    historical_match_count INTEGER NOT NULL,
                    measured_case_count INTEGER NOT NULL,
                    universe_version_id TEXT,
                    universe_size INTEGER,
                    UNIQUE(snapshot_id, horizon_days)
                )
                """
            )
            self._ensure_column(
                connection,
                table="opportunity_ranking_forward_outcomes",
                column="universe_version_id",
                definition="TEXT",
            )
            self._ensure_column(
                connection,
                table="opportunity_ranking_forward_outcomes",
                column="universe_size",
                definition="INTEGER",
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_opportunity_forward_horizon
                ON opportunity_ranking_forward_outcomes(
                    horizon_days,
                    observed_at DESC
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_opportunity_forward_symbol
                ON opportunity_ranking_forward_outcomes(
                    symbol,
                    horizon_days,
                    observed_at DESC
                )
                """
            )

    def save_if_new(self, *, outcome: OpportunityForwardOutcome) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO opportunity_ranking_forward_outcomes (
                    snapshot_id,
                    captured_at,
                    symbol,
                    horizon_days,
                    entry_date,
                    exit_date,
                    observed_at,
                    entry_price,
                    observed_price,
                    return_percent,
                    benchmark_symbol,
                    benchmark_entry_price,
                    benchmark_observed_price,
                    benchmark_return_percent,
                    alpha_percent,
                    maximum_favourable_excursion_percent,
                    maximum_drawdown_percent,
                    status,
                    original_rank,
                    opportunity_score,
                    calibrated_confidence,
                    expected_return_percent,
                    evidence_coverage_percent,
                    eligible_for_execution,
                    category,
                    sector,
                    historical_match_count,
                    measured_case_count,
                    universe_version_id,
                    universe_size
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    outcome.snapshot_id,
                    outcome.captured_at.astimezone(timezone.utc).isoformat(),
                    outcome.symbol,
                    outcome.horizon_days,
                    outcome.entry_date.isoformat(),
                    outcome.exit_date.isoformat(),
                    outcome.observed_at.astimezone(timezone.utc).isoformat(),
                    outcome.entry_price,
                    outcome.observed_price,
                    outcome.return_percent,
                    outcome.benchmark_symbol,
                    outcome.benchmark_entry_price,
                    outcome.benchmark_observed_price,
                    outcome.benchmark_return_percent,
                    outcome.alpha_percent,
                    outcome.maximum_favourable_excursion_percent,
                    outcome.maximum_drawdown_percent,
                    outcome.status,
                    outcome.original_rank,
                    outcome.opportunity_score,
                    outcome.calibrated_confidence,
                    outcome.expected_return_percent,
                    outcome.evidence_coverage_percent,
                    int(outcome.eligible_for_execution),
                    outcome.category,
                    outcome.sector,
                    outcome.historical_match_count,
                    outcome.measured_case_count,
                    outcome.universe_version_id,
                    outcome.universe_size,
                ),
            )
            connection.commit()
            return cursor.rowcount == 1

    def completed_horizons(self, *, snapshot_id: int) -> tuple[int, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT horizon_days
                FROM opportunity_ranking_forward_outcomes
                WHERE snapshot_id = ?
                ORDER BY horizon_days ASC
                """,
                (snapshot_id,),
            ).fetchall()
        return tuple(int(row[0]) for row in rows)

    def list_all(
        self,
        *,
        horizon_days: int | None = None,
        limit: int = 20000,
    ) -> tuple[OpportunityForwardOutcome, ...]:
        if limit <= 0:
            return ()
        if horizon_days is None:
            query = """
                SELECT *
                FROM opportunity_ranking_forward_outcomes
                ORDER BY observed_at DESC, outcome_id DESC
                LIMIT ?
            """
            parameters: tuple[object, ...] = (limit,)
        else:
            query = """
                SELECT *
                FROM opportunity_ranking_forward_outcomes
                WHERE horizon_days = ?
                ORDER BY observed_at DESC, outcome_id DESC
                LIMIT ?
            """
            parameters = (horizon_days, limit)
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return tuple(self._row_to_outcome(row) for row in rows)

    @staticmethod
    def _ensure_column(
        connection: sqlite3.Connection,
        *,
        table: str,
        column: str,
        definition: str,
    ) -> None:
        columns = {
            str(row[1])
            for row in connection.execute(
                f"PRAGMA table_info({table})"
            ).fetchall()
        }
        if column not in columns:
            connection.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _row_to_outcome(row: sqlite3.Row) -> OpportunityForwardOutcome:
        return OpportunityForwardOutcome(
            outcome_id=int(row["outcome_id"]),
            snapshot_id=int(row["snapshot_id"]),
            captured_at=datetime.fromisoformat(str(row["captured_at"])).astimezone(
                timezone.utc
            ),
            symbol=str(row["symbol"]),
            horizon_days=int(row["horizon_days"]),
            entry_date=date.fromisoformat(str(row["entry_date"])),
            exit_date=date.fromisoformat(str(row["exit_date"])),
            observed_at=datetime.fromisoformat(str(row["observed_at"])).astimezone(
                timezone.utc
            ),
            entry_price=float(row["entry_price"]),
            observed_price=float(row["observed_price"]),
            return_percent=float(row["return_percent"]),
            benchmark_symbol=str(row["benchmark_symbol"]),
            benchmark_entry_price=float(row["benchmark_entry_price"]),
            benchmark_observed_price=float(row["benchmark_observed_price"]),
            benchmark_return_percent=float(row["benchmark_return_percent"]),
            alpha_percent=float(row["alpha_percent"]),
            maximum_favourable_excursion_percent=float(
                row["maximum_favourable_excursion_percent"]
            ),
            maximum_drawdown_percent=float(
                row["maximum_drawdown_percent"]
            ),
            status=str(row["status"]),
            original_rank=int(row["original_rank"]),
            opportunity_score=float(row["opportunity_score"]),
            calibrated_confidence=float(row["calibrated_confidence"]),
            expected_return_percent=(
                None
                if row["expected_return_percent"] is None
                else float(row["expected_return_percent"])
            ),
            evidence_coverage_percent=float(row["evidence_coverage_percent"]),
            eligible_for_execution=bool(row["eligible_for_execution"]),
            category=str(row["category"]),
            sector=str(row["sector"]),
            historical_match_count=int(row["historical_match_count"]),
            measured_case_count=int(row["measured_case_count"]),
            universe_version_id=(
                None
                if "universe_version_id" not in set(row.keys())
                or row["universe_version_id"] is None
                else str(row["universe_version_id"])
            ),
            universe_size=(
                None
                if "universe_size" not in set(row.keys())
                or row["universe_size"] is None
                else int(row["universe_size"])
            ),
        )
