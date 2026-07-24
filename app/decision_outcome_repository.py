import sqlite3
from datetime import date, datetime
from pathlib import Path

from app.decision_outcome_models import (
    DecisionOutcomeObservation,
)


class DecisionOutcomeRepository:
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
                decision_outcomes (
                    outcome_id TEXT PRIMARY KEY,
                    decision_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    horizon_days INTEGER NOT NULL,
                    target_date TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    observed_price REAL NOT NULL,
                    absolute_return REAL NOT NULL,
                    benchmark_symbol TEXT NOT NULL,
                    benchmark_entry_price REAL
                        NOT NULL,
                    benchmark_observed_price REAL
                        NOT NULL,
                    benchmark_return REAL NOT NULL,
                    alpha REAL NOT NULL,
                    maximum_favourable_excursion
                        REAL NOT NULL,
                    maximum_drawdown REAL NOT NULL,
                    status TEXT NOT NULL,
                    UNIQUE (
                        decision_id,
                        horizon_days
                    )
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                ix_decision_outcomes_decision
                ON decision_outcomes (
                    decision_id,
                    horizon_days
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                ix_decision_outcomes_observed
                ON decision_outcomes (
                    observed_at DESC
                )
                """
            )
            connection.commit()

    def save_if_new(
        self,
        *,
        observation: (
            DecisionOutcomeObservation
        ),
    ) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO
                decision_outcomes (
                    outcome_id,
                    decision_id,
                    symbol,
                    horizon_days,
                    target_date,
                    observed_at,
                    entry_price,
                    observed_price,
                    absolute_return,
                    benchmark_symbol,
                    benchmark_entry_price,
                    benchmark_observed_price,
                    benchmark_return,
                    alpha,
                    maximum_favourable_excursion,
                    maximum_drawdown,
                    status
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    observation.outcome_id,
                    observation.decision_id,
                    observation.symbol,
                    observation.horizon_days,
                    (
                        observation
                        .target_date
                        .isoformat()
                    ),
                    (
                        observation
                        .observed_at
                        .isoformat()
                    ),
                    observation.entry_price,
                    observation.observed_price,
                    observation.absolute_return,
                    observation.benchmark_symbol,
                    (
                        observation
                        .benchmark_entry_price
                    ),
                    (
                        observation
                        .benchmark_observed_price
                    ),
                    observation.benchmark_return,
                    observation.alpha,
                    (
                        observation
                        .maximum_favourable_excursion
                    ),
                    (
                        observation
                        .maximum_drawdown
                    ),
                    observation.status,
                ),
            )
            connection.commit()
            return cursor.rowcount == 1

    def list_for_decision(
        self,
        *,
        decision_id: str,
    ) -> tuple[
        DecisionOutcomeObservation,
        ...
    ]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    outcome_id,
                    decision_id,
                    symbol,
                    horizon_days,
                    target_date,
                    observed_at,
                    entry_price,
                    observed_price,
                    absolute_return,
                    benchmark_symbol,
                    benchmark_entry_price,
                    benchmark_observed_price,
                    benchmark_return,
                    alpha,
                    maximum_favourable_excursion,
                    maximum_drawdown,
                    status
                FROM decision_outcomes
                WHERE decision_id = ?
                ORDER BY horizon_days ASC
                """,
                (decision_id,),
            ).fetchall()

        return tuple(
            self._from_row(row)
            for row in rows
        )

    def list_recent(
        self,
        *,
        limit: int = 50,
    ) -> tuple[
        DecisionOutcomeObservation,
        ...
    ]:
        if limit <= 0:
            raise ValueError(
                "Limit must be positive."
            )

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    outcome_id,
                    decision_id,
                    symbol,
                    horizon_days,
                    target_date,
                    observed_at,
                    entry_price,
                    observed_price,
                    absolute_return,
                    benchmark_symbol,
                    benchmark_entry_price,
                    benchmark_observed_price,
                    benchmark_return,
                    alpha,
                    maximum_favourable_excursion,
                    maximum_drawdown,
                    status
                FROM decision_outcomes
                ORDER BY observed_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return tuple(
            self._from_row(row)
            for row in rows
        )

    def completed_horizons(
        self,
        *,
        decision_id: str,
    ) -> tuple[int, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT horizon_days
                FROM decision_outcomes
                WHERE decision_id = ?
                ORDER BY horizon_days ASC
                """,
                (decision_id,),
            ).fetchall()

        return tuple(
            int(row[0])
            for row in rows
        )

    def count_all(
        self,
    ) -> int:
        return self._count(
            """
            SELECT COUNT(*)
            FROM decision_outcomes
            """
        )

    def count_decisions(
        self,
    ) -> int:
        return self._count(
            """
            SELECT COUNT(
                DISTINCT decision_id
            )
            FROM decision_outcomes
            """
        )

    def count_positive(
        self,
    ) -> int:
        return self._count(
            """
            SELECT COUNT(*)
            FROM decision_outcomes
            WHERE absolute_return > 0
            """
        )

    def count_negative(
        self,
    ) -> int:
        return self._count(
            """
            SELECT COUNT(*)
            FROM decision_outcomes
            WHERE absolute_return < 0
            """
        )

    def average_return(
        self,
    ) -> float | None:
        return self._average(
            """
            SELECT AVG(absolute_return)
            FROM decision_outcomes
            """
        )

    def average_alpha(
        self,
    ) -> float | None:
        return self._average(
            """
            SELECT AVG(alpha)
            FROM decision_outcomes
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

    def _average(
        self,
        query: str,
    ) -> float | None:
        with self._connect() as connection:
            row = connection.execute(
                query
            ).fetchone()

        if row[0] is None:
            return None

        return round(
            float(row[0]),
            6,
        )

    def _connect(
        self,
    ) -> sqlite3.Connection:
        return sqlite3.connect(
            self._database_path
        )

    @staticmethod
    def _from_row(
        row: tuple[object, ...],
    ) -> DecisionOutcomeObservation:
        return DecisionOutcomeObservation(
            outcome_id=str(row[0]),
            decision_id=str(row[1]),
            symbol=str(row[2]),
            horizon_days=int(row[3]),
            target_date=(
                date.fromisoformat(
                    str(row[4])
                )
            ),
            observed_at=(
                datetime.fromisoformat(
                    str(row[5])
                )
            ),
            entry_price=float(row[6]),
            observed_price=float(row[7]),
            absolute_return=float(
                row[8]
            ),
            benchmark_symbol=str(row[9]),
            benchmark_entry_price=float(
                row[10]
            ),
            benchmark_observed_price=float(
                row[11]
            ),
            benchmark_return=float(
                row[12]
            ),
            alpha=float(row[13]),
            maximum_favourable_excursion=float(
                row[14]
            ),
            maximum_drawdown=float(
                row[15]
            ),
            status=str(row[16]),
        )
