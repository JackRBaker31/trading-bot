from datetime import date, datetime, timedelta, timezone

import pytest

from app.decision_memory_models import (
    DecisionMemoryCapability,
    DecisionMemoryRecord,
)
from app.decision_outcome_models import DecisionOutcomeObservation
from app.historical_similarity_service import HistoricalSimilarityService
from app.investment_thesis_models import (
    InvestmentThesis,
    InvestmentThesisReport,
    ThesisCapabilityAssessment,
)


NOW = datetime(2026, 7, 27, 12, 0, tzinfo=timezone.utc)


def thesis_capability(
    capability: str,
    score: float | None,
    maximum: float,
    stance: str,
    *,
    status: str = "AVAILABLE",
    event_type: str | None = None,
) -> ThesisCapabilityAssessment:
    evidence = ((f"Event type: {event_type}",) if event_type else ())
    return ThesisCapabilityAssessment(
        capability=capability,
        status=status,
        score=score,
        maximum=maximum,
        confidence=0.9 if score is not None else None,
        stance=stance,
        summary=f"{capability} assessment.",
        evidence=evidence,
        blockers=(),
    )


def memory_capability(
    capability: str,
    score: float | None,
    maximum: float,
    stance: str,
    *,
    status: str = "AVAILABLE",
    event_type: str | None = None,
) -> DecisionMemoryCapability:
    evidence = ((f"Event type: {event_type}",) if event_type else ())
    return DecisionMemoryCapability(
        capability=capability,
        status=status,
        score=score,
        maximum=maximum,
        confidence=0.88 if score is not None else None,
        stance=stance,
        summary=f"{capability} assessment.",
        evidence=evidence,
        blockers=(),
    )


def current_thesis() -> InvestmentThesis:
    return InvestmentThesis(
        thesis_id="current-aapl",
        generated_at=NOW,
        symbol="AAPL",
        recommendation="BUY_CANDIDATE",
        score=84.0,
        available_score=84.0,
        available_maximum=100.0,
        confidence=0.90,
        confidence_coverage=0.90,
        risk_tier="MEDIUM",
        time_horizon="SWING",
        suggested_position_value=2500.0,
        eligible_for_execution=False,
        headline="Apple raises guidance.",
        primary_driver="NEWS",
        capabilities=(
            thesis_capability("NEWS", 22.0, 25.0, "BULLISH", event_type="EARNINGS"),
            thesis_capability("TECHNICAL", 16.0, 20.0, "BULLISH"),
            thesis_capability("MACRO", 7.0, 10.0, "SUPPORTIVE"),
            thesis_capability("VALUATION", None, 10.0, "UNKNOWN", status="UNAVAILABLE"),
            thesis_capability("PORTFOLIO", 10.0, 10.0, "SUPPORTIVE"),
            thesis_capability("RISK", 12.0, 15.0, "PASS"),
        ),
        reasons=("Strong evidence.",),
        blockers=("Graduation incomplete.",),
        warnings=(),
    )


def historical_decision(
    *,
    decision_id: str,
    symbol: str,
    days_ago: int,
    score: float,
    confidence: float,
    recommendation: str = "BUY_CANDIDATE",
    risk_tier: str = "MEDIUM",
    time_horizon: str = "SWING",
    primary_driver: str = "NEWS",
    news_score: float = 21.0,
    technical_score: float = 15.0,
    news_stance: str = "BULLISH",
    event_type: str = "EARNINGS",
) -> DecisionMemoryRecord:
    generated_at = NOW - timedelta(days=days_ago)
    return DecisionMemoryRecord(
        decision_id=decision_id,
        fingerprint=f"fingerprint-{decision_id}",
        captured_at=generated_at + timedelta(minutes=1),
        thesis_generated_at=generated_at,
        symbol=symbol,
        recommendation=recommendation,
        score=score,
        confidence=confidence,
        confidence_coverage=0.90,
        risk_tier=risk_tier,
        time_horizon=time_horizon,
        suggested_position_value=0.0,
        eligible_for_execution=False,
        headline=f"Historical {symbol} setup.",
        primary_driver=primary_driver,
        capabilities=(
            memory_capability("NEWS", news_score, 25.0, news_stance, event_type=event_type),
            memory_capability("TECHNICAL", technical_score, 20.0, "BULLISH"),
            memory_capability("MACRO", 6.5, 10.0, "SUPPORTIVE"),
            memory_capability("VALUATION", None, 10.0, "UNKNOWN", status="UNAVAILABLE"),
            memory_capability("PORTFOLIO", 10.0, 10.0, "SUPPORTIVE"),
            memory_capability("RISK", 12.0, 15.0, "PASS"),
        ),
        reasons=(),
        blockers=(),
        warnings=(),
        executed=False,
        paper_trade_id=None,
    )


def outcome(
    *,
    decision_id: str,
    symbol: str,
    return_value: float,
    horizon_days: int = 7,
) -> DecisionOutcomeObservation:
    return DecisionOutcomeObservation(
        outcome_id=f"outcome-{decision_id}-{horizon_days}",
        decision_id=decision_id,
        symbol=symbol,
        horizon_days=horizon_days,
        target_date=date(2026, 7, 20),
        observed_at=NOW - timedelta(days=1),
        entry_price=100.0,
        observed_price=100.0 * (1 + return_value),
        absolute_return=return_value,
        benchmark_symbol="SPY",
        benchmark_entry_price=100.0,
        benchmark_observed_price=101.0,
        benchmark_return=0.01,
        alpha=return_value - 0.01,
        maximum_favourable_excursion=max(return_value, 0.02),
        maximum_drawdown=min(return_value, -0.01),
        status="MEASURED",
    )


def report() -> InvestmentThesisReport:
    return InvestmentThesisReport(
        generated_at=NOW,
        thesis_count=1,
        executable_count=0,
        complete_capability_count=5,
        required_capability_count=6,
        theses=(current_thesis(),),
        platform_blockers=(),
        warnings=(),
    )


def test_matches_feature_vectors_and_summarises_measured_outcomes() -> None:
    close_same_symbol = historical_decision(
        decision_id="close-aapl",
        symbol="AAPL",
        days_ago=30,
        score=82.0,
        confidence=0.88,
    )
    close_cross_symbol = historical_decision(
        decision_id="close-msft",
        symbol="MSFT",
        days_ago=60,
        score=80.0,
        confidence=0.86,
    )
    distant = historical_decision(
        decision_id="distant-tsla",
        symbol="TSLA",
        days_ago=90,
        score=35.0,
        confidence=0.45,
        recommendation="AVOID",
        risk_tier="HIGH",
        time_horizon="POSITION",
        primary_driver="TECHNICAL",
        news_score=4.0,
        technical_score=3.0,
        news_stance="BEARISH",
        event_type="REGULATORY",
    )
    outcomes = {
        "close-aapl": (outcome(decision_id="close-aapl", symbol="AAPL", return_value=0.05),),
        "close-msft": (outcome(decision_id="close-msft", symbol="MSFT", return_value=-0.02),),
    }

    service = HistoricalSimilarityService(
        thesis_provider=(
            lambda symbol: (
                current_thesis()
                if symbol == "AAPL"
                else None
            )
        ),
        decisions_provider=lambda limit: (
            close_same_symbol,
            close_cross_symbol,
            distant,
        )[:limit],
        outcomes_provider=lambda decision_id: outcomes.get(decision_id, ()),
        now_provider=lambda: NOW,
    )

    result = service.analyse(symbol="aapl", minimum_similarity_percent=65.0)

    assert result.symbol == "AAPL"
    assert result.candidate_count == 3
    assert result.matched_case_count == 2
    assert result.measured_case_count == 2
    assert result.win_rate_percent == 50.0
    assert result.average_return_percent == 1.5
    assert result.average_directional_return_percent == 1.5
    assert result.average_holding_days == 7.0
    assert result.sample_quality == "INSUFFICIENT"
    assert result.cases[0].decision_id == "close-aapl"
    assert result.cases[0].same_symbol is True
    assert result.cases[0].similarity_percent > result.cases[1].similarity_percent
    assert any(
        item.code == "CAPABILITY_PROFILE"
        for item in result.cases[0].feature_comparisons
    )


def test_bearish_historical_case_uses_direction_adjusted_success() -> None:
    bearish = historical_decision(
        decision_id="bearish",
        symbol="AAPL",
        days_ago=45,
        score=83.0,
        confidence=0.89,
        recommendation="AVOID",
        news_stance="BEARISH",
    )
    bearish_current = current_thesis()
    bearish_current = InvestmentThesis(
        **{
            **bearish_current.__dict__,
            "recommendation": "AVOID",
            "capabilities": tuple(
                thesis_capability(
                    item.capability,
                    item.score,
                    item.maximum,
                    "BEARISH" if item.capability == "NEWS" else item.stance,
                    status=item.status,
                    event_type="EARNINGS" if item.capability == "NEWS" else None,
                )
                for item in bearish_current.capabilities
            ),
        }
    )
    bearish_report = InvestmentThesisReport(
        generated_at=NOW,
        thesis_count=1,
        executable_count=0,
        complete_capability_count=5,
        required_capability_count=6,
        theses=(bearish_current,),
        platform_blockers=(),
        warnings=(),
    )

    service = HistoricalSimilarityService(
        thesis_provider=(
            lambda symbol: (
                bearish_report.theses[0]
                if symbol == "AAPL"
                else None
            )
        ),
        decisions_provider=lambda limit: (bearish,),
        outcomes_provider=lambda decision_id: (
            outcome(decision_id=decision_id, symbol="AAPL", return_value=-0.04),
        ),
        now_provider=lambda: NOW,
    )

    result = service.analyse(symbol="AAPL", minimum_similarity_percent=50.0)

    assert result.measured_case_count == 1
    assert result.win_rate_percent == 100.0
    assert result.average_return_percent == -4.0
    assert result.average_directional_return_percent == 4.0
    assert result.cases[0].outcome is not None
    assert result.cases[0].outcome.directional_success is True


def test_rejects_symbol_without_current_thesis() -> None:
    service = HistoricalSimilarityService(
        thesis_provider=lambda symbol: None,
        decisions_provider=lambda limit: (),
        outcomes_provider=lambda decision_id: (),
        now_provider=lambda: NOW,
    )

    with pytest.raises(LookupError, match="MSFT"):
        service.analyse(symbol="MSFT")
