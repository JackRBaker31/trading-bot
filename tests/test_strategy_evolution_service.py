from app.adaptive_intelligence_models import (
    ConfidenceBandPerformance,
    PerformanceIntelligence,
)
from app.strategy_evolution_repository import (
    StrategyEvolutionRepository,
)
from app.strategy_evolution_service import (
    StrategyEvolutionService,
)


def test_creates_review_only_calibration_proposal(
    tmp_path,
) -> None:
    repository = StrategyEvolutionRepository(
        database_path=str(
            tmp_path / "application.db"
        )
    )
    service = StrategyEvolutionService(
        repository=repository
    )
    service.initialize()

    performance = PerformanceIntelligence(
        observation_count=25,
        tracked_decision_count=25,
        positive_rate=0.60,
        average_return=0.01,
        average_alpha=0.0,
        best_horizon_days=7,
        confidence_bands=(
            ConfidenceBandPerformance(
                band="90-100%",
                sample_count=25,
                predicted_midpoint=0.95,
                positive_rate=0.60,
                average_return=0.01,
                average_alpha=0.0,
                calibration_gap=-0.35,
            ),
        ),
        learning_confidence=0.1,
        findings=(),
    )

    proposals = service.propose(
        performance=performance
    )

    assert len(proposals) == 1
    assert proposals[0].status == "PROPOSED"
    assert (
        "Manual review is required."
        in proposals[0].safeguards
    )
    assert len(service.recent()) == 1
