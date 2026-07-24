import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.adaptive_intelligence_models import (
    StrategyEvolutionProposal,
)


class StrategyEvolutionRepository:
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
        with sqlite3.connect(
            self._database_path
        ) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS
                strategy_evolution_proposals (
                    proposal_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    title TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    target TEXT NOT NULL,
                    current_value REAL,
                    proposed_value REAL,
                    evidence_json TEXT NOT NULL,
                    safeguards_json TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def save(
        self,
        *,
        proposal: StrategyEvolutionProposal,
    ) -> None:
        with sqlite3.connect(
            self._database_path
        ) as connection:
            connection.execute(
                """
                INSERT INTO
                strategy_evolution_proposals (
                    proposal_id,
                    created_at,
                    status,
                    title,
                    rationale,
                    target,
                    current_value,
                    proposed_value,
                    evidence_json,
                    safeguards_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal.proposal_id,
                    proposal.created_at.isoformat(),
                    proposal.status,
                    proposal.title,
                    proposal.rationale,
                    proposal.target,
                    proposal.current_value,
                    proposal.proposed_value,
                    json.dumps(
                        list(proposal.evidence)
                    ),
                    json.dumps(
                        list(proposal.safeguards)
                    ),
                ),
            )
            connection.commit()

    def list_recent(
        self,
        *,
        limit: int = 20,
    ) -> tuple[
        StrategyEvolutionProposal,
        ...
    ]:
        with sqlite3.connect(
            self._database_path
        ) as connection:
            rows = connection.execute(
                """
                SELECT
                    proposal_id,
                    created_at,
                    status,
                    title,
                    rationale,
                    target,
                    current_value,
                    proposed_value,
                    evidence_json,
                    safeguards_json
                FROM strategy_evolution_proposals
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return tuple(
            StrategyEvolutionProposal(
                proposal_id=str(row[0]),
                created_at=(
                    datetime.fromisoformat(
                        str(row[1])
                    )
                ),
                status=str(row[2]),
                title=str(row[3]),
                rationale=str(row[4]),
                target=str(row[5]),
                current_value=(
                    float(row[6])
                    if row[6] is not None
                    else None
                ),
                proposed_value=(
                    float(row[7])
                    if row[7] is not None
                    else None
                ),
                evidence=tuple(
                    json.loads(
                        str(row[8])
                    )
                ),
                safeguards=tuple(
                    json.loads(
                        str(row[9])
                    )
                ),
            )
            for row in rows
        )
