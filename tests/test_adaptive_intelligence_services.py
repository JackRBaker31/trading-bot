from app.performance_intelligence_service import (
    PerformanceIntelligenceService,
)
from app.portfolio_optimisation_service import (
    PortfolioOptimisationService,
)
from app.risk_attribution_service import (
    RiskAttributionService,
)


def test_performance_intelligence_links_decisions_and_outcomes(
) -> None:
    result = PerformanceIntelligenceService().analyse(
        decisions=(
            {
                "decision_id": "D1",
                "confidence": 0.85,
            },
        ),
        outcomes=(
            {
                "decision_id": "D1",
                "absolute_return": 0.05,
                "alpha": 0.02,
                "horizon_days": 7,
            },
        ),
    )

    assert result.observation_count == 1
    assert result.positive_rate == 1.0
    assert result.average_return == 0.05


def test_portfolio_optimisation_caps_symbol_weight(
) -> None:
    result = PortfolioOptimisationService().optimise(
        theses=(
            {
                "symbol": "AAPL",
                "recommendation": "BUY_CANDIDATE",
                "eligible_for_execution": True,
                "score": 90.0,
                "confidence": 0.90,
                "risk_tier": "LOW",
            },
        ),
        available_cash=10000.0,
        maximum_portfolio_exposure_ratio=0.8,
        maximum_symbol_weight=0.25,
    )

    assert len(result.allocations) == 1
    assert (
        result.allocations[0]
        .constrained_weight
        == 0.25
    )
    assert (
        result.allocations[0]
        .suggested_value
        == 2000.0
    )


def test_risk_attribution_identifies_incomplete_thesis(
) -> None:
    result = RiskAttributionService().analyse(
        theses=(
            {
                "confidence_coverage": 0.8,
                "blockers": [
                    "Valuation missing."
                ],
                "risk_tier": "HIGH",
            },
        ),
        portfolio={
            "cash": 8000.0,
            "starting_cash": 10000.0,
        },
    )

    assert result.overall_risk_score > 0
    assert (
        result.dominant_risk
        is not None
    )
