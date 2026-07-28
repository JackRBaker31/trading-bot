from datetime import datetime, timezone
from types import SimpleNamespace

from app.opportunity_ranking_service import OpportunityRankingService


NOW = datetime(2026, 7, 28, 8, 30, tzinfo=timezone.utc)


def capability(
    name: str,
    score: float | None,
    maximum: float,
    status: str = "AVAILABLE",
):
    return SimpleNamespace(
        capability=name,
        score=score,
        maximum=maximum,
        status=status,
    )


def thesis(
    *,
    symbol: str,
    score: float,
    confidence: float,
    coverage: float,
    eligible: bool,
    risk_tier: str,
    technical: float,
    macro: float,
    blockers: tuple[str, ...] = (),
):
    return SimpleNamespace(
        symbol=symbol,
        score=score,
        confidence=confidence,
        confidence_coverage=coverage,
        eligible_for_execution=eligible,
        risk_tier=risk_tier,
        recommendation=("BUY_CANDIDATE" if eligible else "BLOCKED"),
        headline=f"{symbol} current opportunity.",
        generated_at=NOW,
        capabilities=(
            capability("TECHNICAL", technical, 20.0),
            capability("MACRO", macro, 10.0),
        ),
        blockers=blockers,
        warnings=(),
    )


def similarity(
    *,
    symbol: str,
    matches: int,
    measured: int,
    win_rate: float | None,
    directional_return: float | None,
):
    return SimpleNamespace(
        symbol=symbol,
        matched_case_count=matches,
        measured_case_count=measured,
        average_similarity_percent=82.0 if matches else None,
        win_rate_percent=win_rate,
        average_directional_return_percent=directional_return,
        warnings=(),
    )


def performance() -> dict[str, object]:
    return {
        "confidence_calibration": {
            "calibration_buckets": [
                {
                    "label": "80–89%",
                    "measured_count": 4,
                    "actual_accuracy_percent": 75.0,
                },
                {
                    "label": "90%+",
                    "measured_count": 8,
                    "actual_accuracy_percent": 70.0,
                },
            ]
        },
        "symbol_analytics": [
            {
                "symbol": "AAPL",
                "sector": "Technology",
                "measured_count": 8,
                "directional_accuracy_percent": 75.0,
                "average_return_percent": 2.2,
            },
            {
                "symbol": "LLY",
                "sector": "Healthcare",
                "measured_count": 2,
                "directional_accuracy_percent": 50.0,
                "average_return_percent": 0.5,
            },
        ],
        "sector_analytics": [
            {
                "sector": "Technology",
                "measured_count": 16,
                "directional_accuracy_percent": 68.0,
                "average_return_percent": 1.4,
            },
            {
                "sector": "Healthcare",
                "measured_count": 4,
                "directional_accuracy_percent": 50.0,
                "average_return_percent": 0.2,
            },
        ],
    }


def test_ranks_stronger_evidence_first_without_bypassing_blockers() -> None:
    aapl = thesis(
        symbol="AAPL",
        score=89.0,
        confidence=0.92,
        coverage=0.90,
        eligible=False,
        risk_tier="LOW",
        technical=18.0,
        macro=8.5,
        blockers=("Graduation sample is incomplete.",),
    )
    lly = thesis(
        symbol="LLY",
        score=73.0,
        confidence=0.84,
        coverage=0.68,
        eligible=True,
        risk_tier="MEDIUM",
        technical=13.0,
        macro=6.0,
    )
    similarity_by_symbol = {
        "AAPL": similarity(
            symbol="AAPL",
            matches=9,
            measured=7,
            win_rate=71.4,
            directional_return=3.1,
        ),
        "LLY": similarity(
            symbol="LLY",
            matches=2,
            measured=1,
            win_rate=100.0,
            directional_return=0.4,
        ),
    }
    service = OpportunityRankingService(
        thesis_report_provider=lambda: SimpleNamespace(
            theses=(aapl, lly),
            warnings=(),
        ),
        similarity_provider=lambda current: similarity_by_symbol[current.symbol],
        performance_review_provider=performance,
        market_health_provider=lambda: {
            "status": "HEALTHY",
            "circuit_state": "CLOSED",
        },
        now_provider=lambda: NOW,
    )

    report = service.get_report()

    assert sum(report.component_weights.values()) == 100.0
    assert report.advisory_only is True
    assert report.items[0].symbol == "AAPL"
    assert report.items[0].eligible_for_execution is False
    assert report.items[0].category == "HIGH_POTENTIAL_BLOCKED"
    assert "Graduation sample is incomplete." in report.items[0].blockers
    assert report.items[1].rank == 2
    assert report.items[0].expected_return_percent is not None


def test_missing_measured_evidence_is_not_fabricated() -> None:
    nvda = thesis(
        symbol="NVDA",
        score=70.0,
        confidence=0.78,
        coverage=0.45,
        eligible=False,
        risk_tier="HIGH",
        technical=12.0,
        macro=5.0,
        blockers=("Execution permission is not confirmed.",),
    )
    service = OpportunityRankingService(
        thesis_report_provider=lambda: SimpleNamespace(
            theses=(nvda,),
            warnings=(),
        ),
        similarity_provider=lambda current: similarity(
            symbol=current.symbol,
            matches=0,
            measured=0,
            win_rate=None,
            directional_return=None,
        ),
        performance_review_provider=lambda: {
            "confidence_calibration": {"calibration_buckets": []},
            "symbol_analytics": [],
            "sector_analytics": [],
        },
        market_health_provider=lambda: {
            "status": "DEGRADED",
            "circuit_state": "OPEN",
        },
        now_provider=lambda: NOW,
    )

    item = service.get_report().items[0]

    assert item.expected_return_percent is None
    assert item.calibrated_confidence == item.raw_confidence
    assert item.confidence_sample_count == 0
    assert item.data_quality == "LIMITED"
    assert any(
        component.code == "EXPECTED_RETURN"
        and component.status == "UNAVAILABLE"
        and component.value == 0.0
        for component in item.components
    )
