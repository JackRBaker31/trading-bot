from datetime import (
    datetime,
    timezone,
)

from app.copilot_intelligence_models import (
    CopilotGraduationCheck,
    CopilotGraduationOverview,
    CopilotIntelligenceOverview,
)
from app.copilot_overview_models import (
    CopilotActivityOverview,
    CopilotFailuresOverview,
    CopilotOverview,
    CopilotPlatformOverview,
)
from app.decision_intelligence_service import (
    DecisionIntelligenceService,
)
from app.decision_trace_repository import (
    DecisionTraceRepository,
)


NOW = datetime(
    2026,
    7,
    24,
    11,
    0,
    tzinfo=timezone.utc,
)


def build_overview(
) -> CopilotOverview:
    return CopilotOverview(
        generated_at=NOW,
        overall_status="HEALTHY",
        platform=(
            CopilotPlatformOverview(
                overall_status=(
                    "HEALTHY"
                ),
                online_services=5,
                required_services=5,
            )
        ),
        activity=(
            CopilotActivityOverview(
                running_jobs=0,
                queued_jobs=0,
            )
        ),
        schedule=None,
        failures=(
            CopilotFailuresOverview(
                recent_count=0,
                latest=None,
            )
        ),
        trading_intelligence=(
            CopilotIntelligenceOverview(
                trading_readiness=(
                    "NOT_READY"
                ),
                market_outlook=(
                    "CAUTIOUS"
                ),
                confidence=63.5,
                signal_count=12,
                actionable_signal_count=2,
                evidence_quality="LOW",
            )
        ),
        graduation=(
            CopilotGraduationOverview(
                ready=False,
                passed_checks=1,
                total_checks=2,
                checks=(
                    CopilotGraduationCheck(
                        name=(
                            "Decision sample"
                        ),
                        passed=False,
                        reason=(
                            "More shadow "
                            "decisions are "
                            "required."
                        ),
                    ),
                ),
            )
        ),
    )


def create_service(
    tmp_path,
) -> DecisionIntelligenceService:
    service = (
        DecisionIntelligenceService(
            repository=(
                DecisionTraceRepository(
                    database_path=str(
                        tmp_path
                        / "application.db"
                    )
                )
            ),
            overview_provider=(
                build_overview
            ),
            now_provider=lambda: NOW,
        )
    )
    service.initialize()
    return service


def test_builds_no_trade_trace(
    tmp_path,
) -> None:
    trace = create_service(
        tmp_path
    ).capture()

    assert (
        trace.decision
        == "NO_TRADE"
    )
    assert len(trace.stages) == 5
    assert (
        trace.stages[-1].stage
        == "DECISION"
    )
    assert (
        "More shadow decisions "
        "are required."
        in trace.blockers
    )


def test_persists_trace(
    tmp_path,
) -> None:
    service = create_service(
        tmp_path
    )
    service.capture()

    items = service.list_recent(
        limit=10,
        capture_current=False,
    )

    assert len(items) == 1
    assert (
        items[0].confidence
        == 63.5
    )


def test_trace_serialises(
    tmp_path,
) -> None:
    payload = (
        create_service(
            tmp_path
        )
        .capture()
        .to_dictionary()
    )

    assert (
        payload["decision"]
        == "NO_TRADE"
    )
    assert len(
        payload["stages"]
    ) == 5
