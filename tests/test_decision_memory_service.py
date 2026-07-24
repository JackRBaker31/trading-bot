from datetime import datetime, timezone

from app.decision_memory_repository import (
    DecisionMemoryRepository,
)
from app.decision_memory_service import (
    DecisionMemoryService,
)
from app.investment_thesis_models import (
    InvestmentThesis,
    InvestmentThesisReport,
    ThesisCapabilityAssessment,
)


NOW = datetime(
    2026,
    7,
    24,
    16,
    0,
    tzinfo=timezone.utc,
)


def thesis(
    *,
    score: float = 84.5,
) -> InvestmentThesis:
    return InvestmentThesis(
        thesis_id="source-thesis-1",
        generated_at=NOW,
        symbol="AAPL",
        recommendation="INCOMPLETE",
        score=score,
        available_score=50.7,
        available_maximum=60.0,
        confidence=0.91,
        confidence_coverage=0.83,
        risk_tier="HIGH",
        time_horizon="POSITION",
        suggested_position_value=0.0,
        eligible_for_execution=False,
        headline=(
            "Apple raises guidance."
        ),
        primary_driver="NEWS",
        capabilities=(
            ThesisCapabilityAssessment(
                capability="NEWS",
                status="AVAILABLE",
                score=22.0,
                maximum=25.0,
                confidence=0.91,
                stance="BULLISH",
                summary=(
                    "News was supportive."
                ),
                evidence=(
                    "Guidance increased.",
                ),
                blockers=(),
            ),
        ),
        reasons=("Strong news.",),
        blockers=(
            "Valuation unavailable.",
        ),
        warnings=(),
    )


def report(
    *,
    score: float = 84.5,
) -> InvestmentThesisReport:
    return InvestmentThesisReport(
        generated_at=NOW,
        thesis_count=1,
        executable_count=0,
        complete_capability_count=5,
        required_capability_count=6,
        theses=(
            thesis(
                score=score
            ),
        ),
        platform_blockers=(),
        warnings=(),
    )


def create_service(
    tmp_path,
) -> DecisionMemoryService:
    service = DecisionMemoryService(
        repository=(
            DecisionMemoryRepository(
                database_path=str(
                    tmp_path
                    / "application.db"
                )
            )
        ),
        now_provider=lambda: NOW,
    )
    service.initialize()
    return service


def test_captures_report_and_deduplicates(
    tmp_path,
) -> None:
    service = create_service(
        tmp_path
    )

    first = service.capture_report(
        report=report()
    )
    second = service.capture_report(
        report=report()
    )

    assert first.captured_count == 1
    assert first.duplicate_count == 0
    assert second.captured_count == 0
    assert second.duplicate_count == 1
    assert (
        service.overview().total_count
        == 1
    )


def test_material_change_creates_new_record(
    tmp_path,
) -> None:
    service = create_service(
        tmp_path
    )

    service.capture_report(
        report=report(
            score=84.5
        )
    )
    result = service.capture_report(
        report=report(
            score=87.0
        )
    )

    assert result.captured_count == 1
    assert (
        service.overview().total_count
        == 2
    )
