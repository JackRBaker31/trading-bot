from datetime import datetime, timedelta, timezone

from app.copilot_change_service import CopilotChangeService
from app.copilot_history_repository import CopilotHistoryRepository
from app.copilot_intelligence_models import (
    CopilotGraduationCheck, CopilotGraduationOverview,
    CopilotIntelligenceOverview,
)
from app.copilot_overview_models import (
    CopilotActivityOverview, CopilotFailuresOverview,
    CopilotOverview, CopilotPlatformOverview,
)


NOW = datetime(2026, 7, 24, 10, 0, tzinfo=timezone.utc)


def overview(
    *, confidence: float, actionable: int,
    passed: int, reason: str | None,
) -> CopilotOverview:
    checks = () if reason is None else (
        CopilotGraduationCheck(
            name="Decision sample", passed=False, reason=reason,
        ),
    )
    return CopilotOverview(
        generated_at=NOW, overall_status="HEALTHY",
        platform=CopilotPlatformOverview(
            overall_status="HEALTHY", online_services=5, required_services=5,
        ),
        activity=CopilotActivityOverview(running_jobs=0, queued_jobs=0),
        schedule=None,
        failures=CopilotFailuresOverview(recent_count=0, latest=None),
        trading_intelligence=CopilotIntelligenceOverview(
            trading_readiness="NOT_READY", market_outlook="CAUTIOUS",
            confidence=confidence, signal_count=12,
            actionable_signal_count=actionable, evidence_quality="LOW",
        ),
        graduation=CopilotGraduationOverview(
            ready=False, passed_checks=passed, total_checks=2, checks=checks,
        ),
    )


def test_first_capture_has_no_comparison(tmp_path) -> None:
    service = CopilotChangeService(
        repository=CopilotHistoryRepository(
            database_path=str(tmp_path / "application.db"),
        ),
        overview_provider=lambda: overview(
            confidence=60, actionable=1, passed=0,
            reason="More decisions are required.",
        ),
        now_provider=lambda: NOW,
    )
    service.initialize()
    result = service.change_summary()
    assert not result.comparison_available
    assert result.current.decision == "NO_TRADE"


def test_detects_change_and_cleared_blocker(tmp_path) -> None:
    clock = [NOW]
    state = [overview(
        confidence=60, actionable=1, passed=0,
        reason="More decisions are required.",
    )]
    service = CopilotChangeService(
        repository=CopilotHistoryRepository(
            database_path=str(tmp_path / "application.db"),
        ),
        overview_provider=lambda: state[0],
        now_provider=lambda: clock[0],
    )
    service.initialize()
    service.capture()

    clock[0] = NOW + timedelta(hours=1)
    state[0] = overview(
        confidence=72.5, actionable=3, passed=1, reason=None,
    )
    result = service.change_summary()

    assert result.comparison_available
    assert result.confidence_change is not None
    assert result.confidence_change.change == 12.5
    assert "More decisions are required." in result.cleared_blockers


def test_repository_persists_history(tmp_path) -> None:
    service = CopilotChangeService(
        repository=CopilotHistoryRepository(
            database_path=str(tmp_path / "application.db"),
        ),
        overview_provider=lambda: overview(
            confidence=63.5, actionable=2, passed=1, reason=None,
        ),
        now_provider=lambda: NOW,
    )
    service.initialize()
    service.capture()
    history = service.list_history(limit=10, capture_current=False)
    assert len(history) == 1
    assert history[0].confidence == 63.5
