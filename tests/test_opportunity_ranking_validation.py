from datetime import date, datetime, timezone

from app.backtest_models import HistoricalPriceBar
from app.opportunity_ranking_history_repository import (
    OpportunityRankingHistoryRepository,
)
from app.opportunity_ranking_models import (
    OpportunityRankingComponent,
    OpportunityRankingReport,
    RankedOpportunity,
)
from app.opportunity_ranking_validation_repository import (
    OpportunityRankingValidationRepository,
)
from app.opportunity_ranking_validation_service import (
    OpportunityRankingValidationService,
)


def _report(*, generated_at: datetime, score: float = 82.0):
    component = OpportunityRankingComponent(
        code="THESIS_QUALITY",
        label="Thesis quality",
        value=14.0,
        maximum=18.0,
        status="AVAILABLE",
        detail="Strong thesis.",
    )
    item = RankedOpportunity(
        rank=1,
        symbol="AAPL",
        opportunity_score=score,
        category="EXECUTION_READY",
        recommendation="BUY_CANDIDATE",
        thesis_score=84.0,
        raw_confidence=0.80,
        calibrated_confidence=0.76,
        confidence_sample_count=12,
        expected_return_percent=3.5,
        evidence_coverage_percent=88.0,
        data_quality="HIGH",
        risk_tier="MODERATE",
        eligible_for_execution=True,
        historical_match_count=8,
        measured_case_count=5,
        sector="Technology",
        headline="Apple setup.",
        generated_at=generated_at,
        components=(component,),
        positive_contributors=("Strong thesis",),
        penalties=(),
        improvement_actions=(),
        blockers=(),
        warnings=(),
    )
    return OpportunityRankingReport(
        generated_at=generated_at,
        methodology_version="KAIRO-ORANK-1.0",
        methodology_summary="Test ranking.",
        advisory_only=True,
        performance_window_days=90,
        ranking_count=1,
        execution_ready_count=1,
        high_potential_blocked_count=0,
        market_data_status="HEALTHY",
        component_weights={"THESIS_QUALITY": 18.0},
        items=(item,),
        warnings=(),
    )


def _bars(symbol: str, prices: list[tuple[date, float, float, float, float]]):
    return [
        HistoricalPriceBar(
            symbol=symbol,
            trading_date=trading_date,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=1000,
        )
        for trading_date, open_price, high_price, low_price, close_price in prices
    ]


def test_captures_forward_returns_from_next_session_open(tmp_path) -> None:
    database_path = str(tmp_path / "application.db")
    history = OpportunityRankingHistoryRepository(database_path=database_path)
    validation = OpportunityRankingValidationRepository(database_path=database_path)
    history.initialize()
    validation.initialize()
    history.record_report(
        report=_report(
            generated_at=datetime(2026, 7, 1, 15, 0, tzinfo=timezone.utc)
        ),
        source="INTELLIGENCE_CYCLE",
    )

    aapl = _bars(
        "AAPL",
        [
            (date(2026, 7, 1), 99, 101, 98, 100),
            (date(2026, 7, 2), 100, 106, 99, 105),
            (date(2026, 7, 3), 105, 107, 103, 104),
            (date(2026, 7, 6), 104, 109, 103, 108),
            (date(2026, 7, 7), 108, 111, 107, 110),
            (date(2026, 7, 8), 110, 113, 109, 112),
        ],
    )
    spy = _bars(
        "SPY",
        [
            (date(2026, 7, 1), 499, 501, 498, 500),
            (date(2026, 7, 2), 500, 506, 499, 505),
            (date(2026, 7, 3), 505, 507, 503, 504),
            (date(2026, 7, 6), 504, 508, 503, 507),
            (date(2026, 7, 7), 507, 510, 506, 509),
            (date(2026, 7, 8), 509, 512, 508, 511),
        ],
    )

    def bars_provider(symbol: str, output_size: int):
        del output_size
        return spy if symbol == "SPY" else aapl

    service = OpportunityRankingValidationService(
        history_repository=history,
        validation_repository=validation,
        bars_provider=bars_provider,
        now_provider=lambda: datetime(2026, 7, 10, 9, 0, tzinfo=timezone.utc),
        horizons=(1, 5),
    )

    result = service.capture_due()
    outcomes = validation.list_all()

    assert result.created_outcome_count == 2
    assert len(outcomes) == 2
    one_day = next(item for item in outcomes if item.horizon_days == 1)
    five_day = next(item for item in outcomes if item.horizon_days == 5)
    assert one_day.entry_date == date(2026, 7, 2)
    assert one_day.entry_price == 100.0
    assert one_day.observed_price == 105.0
    assert one_day.return_percent == 5.0
    assert five_day.exit_date == date(2026, 7, 8)
    assert five_day.return_percent == 12.0


def test_report_builds_score_rank_and_readiness_buckets(tmp_path) -> None:
    database_path = str(tmp_path / "application.db")
    history = OpportunityRankingHistoryRepository(database_path=database_path)
    validation = OpportunityRankingValidationRepository(database_path=database_path)
    history.initialize()
    validation.initialize()
    history.record_report(
        report=_report(
            generated_at=datetime(2026, 7, 1, 15, 0, tzinfo=timezone.utc)
        ),
        source="INTELLIGENCE_CYCLE",
    )

    aapl = _bars(
        "AAPL",
        [
            (date(2026, 7, 2), 100, 106, 99, 105),
            (date(2026, 7, 3), 105, 107, 103, 104),
        ],
    )
    spy = _bars(
        "SPY",
        [
            (date(2026, 7, 2), 500, 506, 499, 505),
            (date(2026, 7, 3), 505, 507, 503, 504),
        ],
    )

    service = OpportunityRankingValidationService(
        history_repository=history,
        validation_repository=validation,
        bars_provider=lambda symbol, output_size: spy if symbol == "SPY" else aapl,
        now_provider=lambda: datetime(2026, 7, 5, 9, 0, tzinfo=timezone.utc),
        horizons=(1,),
    )
    service.capture_due()

    report = service.get_report(horizon_days=1)

    assert report.methodology_version == "KAIRO-RVALID-1.0"
    assert report.selected_horizon.sample_count == 1
    assert report.selected_horizon.hit_rate_percent == 100.0
    assert report.score_bands[0].sample_count == 1
    assert report.rank_buckets[0].sample_count == 1
    assert report.readiness_buckets[0].sample_count == 1
    assert report.latest_outcomes[0].symbol == "AAPL"


def test_rejects_unsupported_report_horizon(tmp_path) -> None:
    service = OpportunityRankingValidationService(
        history_repository=OpportunityRankingHistoryRepository(
            database_path=str(tmp_path / "application.db")
        ),
        validation_repository=OpportunityRankingValidationRepository(
            database_path=str(tmp_path / "application.db")
        ),
        bars_provider=lambda symbol, output_size: [],
        horizons=(1, 5),
    )
    service.initialize()

    try:
        service.get_report(horizon_days=7)
    except ValueError as error:
        assert "1, 5" in str(error)
    else:
        raise AssertionError("Unsupported horizon should fail.")
