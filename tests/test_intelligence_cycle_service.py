from datetime import datetime, timezone
from types import SimpleNamespace

from app.intelligence_cycle_service import IntelligenceCycleService


def _news_result(*, failures: int = 0, stale: int = 0):
    return SimpleNamespace(
        provider_name="TWELVE_DATA",
        symbols=("AAPL", "MSFT"),
        observation_summary=SimpleNamespace(
            article_count=4,
            signal_count=3,
        ),
        snapshot_summary=SimpleNamespace(
            captured_count=2,
            failed_count=failures,
        ),
        outcome_summary=SimpleNamespace(
            recorded_count=1,
            failed_count=0,
            stale_quote_count=stale,
        ),
    )


def _performance():
    return SimpleNamespace(
        total_decision_count=12,
        horizons=(
            SimpleNamespace(
                horizon="1H",
                measured_count=5,
                directional_success_percent=60.0,
                profitable_after_cost_percent=55.0,
            ),
            SimpleNamespace(
                horizon="1D",
                measured_count=3,
                directional_success_percent=66.67,
                profitable_after_cost_percent=60.0,
            ),
        ),
    )


def _service(*, failures: int = 0, stale: int = 0):
    calls: list[str] = []

    def mark(name, value):
        def runner():
            calls.append(name)
            return value
        return runner

    service = IntelligenceCycleService(
        news_cycle_runner=mark(
            "news", _news_result(failures=failures, stale=stale)
        ),
        shadow_analysis_runner=mark(
            "shadow",
            SimpleNamespace(
                to_dictionary=lambda: {
                    "opportunities_seen": 3,
                    "decisions_created": 2,
                    "decisions_skipped": 1,
                }
            ),
        ),
        shadow_performance_runner=mark(
            "performance", _performance()
        ),
        graduation_status_runner=mark(
            "graduation",
            SimpleNamespace(
                status="RESEARCH_ONLY",
                eligible=False,
                checks_passed=2,
                total_checks=7,
            ),
        ),
        intelligence_snapshot_runner=mark(
            "snapshot",
            SimpleNamespace(
                market_outlook=SimpleNamespace(value="CAUTIOUS"),
                confidence=62.5,
                trading_readiness=SimpleNamespace(value="NOT_READY"),
                evidence_quality=SimpleNamespace(value="LIMITED"),
                signal_count=3,
                top_opportunities=(object(),),
                freshness=SimpleNamespace(is_stale=False),
            ),
        ),
        daily_briefing_runner=mark(
            "briefing",
            SimpleNamespace(
                headline="KAIRO is cautious",
                market_outlook="CAUTIOUS",
                trading_readiness="NOT_READY",
                graduation_status="RESEARCH_ONLY",
                is_stale=False,
                actions=(object(), object()),
                warnings=("More evidence required.",),
            ),
        ),
        now_provider=lambda: datetime(
            2026, 7, 21, 20, 0, tzinfo=timezone.utc
        ),
    )
    return service, calls


def test_runs_research_only_stages_in_order() -> None:
    service, calls = _service()

    result = service.run()
    data = result.to_dictionary()

    assert calls == [
        "news",
        "shadow",
        "performance",
        "graduation",
        "snapshot",
        "briefing",
    ]
    assert data["status"] == "SUCCEEDED"
    assert data["trading_impact"] == "NONE"
    assert [stage["stage"] for stage in data["stages"]] == [
        "NEWS_RESEARCH",
        "CAPTURE_PRICE_OUTCOMES",
        "SHADOW_ANALYSIS",
        "SHADOW_PERFORMANCE",
        "GRADUATION_STATUS",
        "INTELLIGENCE_SNAPSHOT",
        "DAILY_BRIEFING",
    ]


def test_price_failures_create_warning_result() -> None:
    service, _ = _service(failures=2, stale=1)

    result = service.run()
    data = result.to_dictionary()
    outcome_stage = data["stages"][1]

    assert result.has_warnings is True
    assert data["status"] == "SUCCEEDED_WITH_WARNINGS"
    assert outcome_stage["status"] == "SUCCEEDED_WITH_WARNINGS"
    assert outcome_stage["detail"]["failure_count"] == 2
    assert len(outcome_stage["warnings"]) == 2