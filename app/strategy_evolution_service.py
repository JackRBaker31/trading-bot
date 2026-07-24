from datetime import datetime, timezone
from uuid import uuid4

from app.adaptive_intelligence_models import (
    PerformanceIntelligence,
    StrategyEvolutionProposal,
)
from app.strategy_evolution_repository import (
    StrategyEvolutionRepository,
)


class StrategyEvolutionService:
    def __init__(
        self,
        *,
        repository: (
            StrategyEvolutionRepository
        ),
    ) -> None:
        self._repository = repository

    def initialize(self) -> None:
        self._repository.initialize()

    def propose(
        self,
        *,
        performance: PerformanceIntelligence,
    ) -> tuple[
        StrategyEvolutionProposal,
        ...
    ]:
        proposals: list[
            StrategyEvolutionProposal
        ] = []

        for band in performance.confidence_bands:
            if (
                band.sample_count < 20
                or band.calibration_gap is None
            ):
                continue

            gap = float(
                band.calibration_gap
            )

            if abs(gap) < 0.08:
                continue

            direction = (
                "reduce"
                if gap < 0
                else "increase"
            )
            proposal = StrategyEvolutionProposal(
                proposal_id=(
                    "EVOLVE-"
                    + uuid4().hex[
                        :12
                    ].upper()
                ),
                created_at=datetime.now(
                    timezone.utc
                ),
                status="PROPOSED",
                title=(
                    f"{direction.title()} confidence "
                    f"calibration for {band.band}"
                ),
                rationale=(
                    "Observed positive-outcome frequency "
                    "materially differs from predicted "
                    "confidence."
                ),
                target=(
                    "confidence_calibration."
                    + band.band
                    .replace("%", "")
                    .replace("-", "_")
                ),
                current_value=1.0,
                proposed_value=round(
                    max(
                        0.80,
                        min(
                            (
                                float(
                                    band.positive_rate
                                )
                                / max(
                                    band.predicted_midpoint,
                                    0.01,
                                )
                            ),
                            1.15,
                        ),
                    ),
                    4,
                ),
                evidence=(
                    f"Sample count: {band.sample_count}.",
                    (
                        "Observed positive rate: "
                        f"{float(band.positive_rate) * 100:.1f}%."
                    ),
                    (
                        "Predicted midpoint: "
                        f"{band.predicted_midpoint * 100:.1f}%."
                    ),
                ),
                safeguards=(
                    "Manual review is required.",
                    "No live strategy parameter is changed.",
                    "Paper-trading validation is required.",
                    "Rollback criteria must be documented.",
                ),
            )
            self._repository.save(
                proposal=proposal
            )
            proposals.append(proposal)

        return tuple(proposals)

    def recent(
        self,
        *,
        limit: int = 20,
    ) -> tuple[
        StrategyEvolutionProposal,
        ...
    ]:
        return self._repository.list_recent(
            limit=limit
        )
