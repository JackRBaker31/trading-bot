from datetime import datetime, timedelta, timezone

from app.opportunity_ranking_history_repository import (
    OpportunityRankingHistoryRepository,
)
from app.opportunity_ranking_history_service import (
    OpportunityRankingHistoryService,
)
from app.opportunity_ranking_models import (
    OpportunityRankingComponent,
    OpportunityRankingReport,
    RankedOpportunity,
)


NOW = datetime(2026, 7, 28, 10, 0, tzinfo=timezone.utc)


def item(
    *,
    symbol: str = "AAPL",
    rank: int = 1,
    score: float = 80.0,
    eligible: bool = False,
    blockers: tuple[str, ...] = ("Graduation incomplete.",),
    thesis_value: float = 15.0,
) -> RankedOpportunity:
    return RankedOpportunity(
        rank=rank,
        symbol=symbol,
        opportunity_score=score,
        category=("PRIORITY_READY" if eligible else "HIGH_POTENTIAL_BLOCKED"),
        recommendation="BUY_CANDIDATE",
        thesis_score=85.0,
        raw_confidence=0.9,
        calibrated_confidence=0.82,
        confidence_sample_count=8,
        expected_return_percent=2.4,
        evidence_coverage_percent=88.0,
        data_quality="MODERATE",
        risk_tier="LOW",
        eligible_for_execution=eligible,
        historical_match_count=7,
        measured_case_count=5,
        sector="Technology",
        headline=f"{symbol} opportunity",
        generated_at=NOW,
        components=(
            OpportunityRankingComponent(
                code="THESIS_QUALITY",
                label="Thesis quality",
                value=thesis_value,
                maximum=18.0,
                status="AVAILABLE",
                detail="Test component.",
            ),
        ),
        positive_contributors=("Strong thesis.",),
        penalties=(),
        improvement_actions=(),
        blockers=blockers,
        warnings=(),
    )


def report(*, generated_at: datetime, items: tuple[RankedOpportunity, ...]):
    return OpportunityRankingReport(
        generated_at=generated_at,
        methodology_version="KAIRO-ORANK-1.0",
        methodology_summary="Test",
        advisory_only=True,
        performance_window_days=90,
        ranking_count=len(items),
        execution_ready_count=sum(1 for value in items if value.eligible_for_execution),
        high_potential_blocked_count=sum(
            1 for value in items if value.category == "HIGH_POTENTIAL_BLOCKED"
        ),
        market_data_status="HEALTHY",
        component_weights={"THESIS_QUALITY": 18.0},
        items=items,
        warnings=(),
    )


def test_deduplicates_unchanged_observations(tmp_path) -> None:
    repository = OpportunityRankingHistoryRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()

    first = repository.record_report(
        report=report(generated_at=NOW, items=(item(),)),
        source="INTELLIGENCE_CYCLE",
    )
    second = repository.record_report(
        report=report(
            generated_at=NOW + timedelta(minutes=30),
            items=(item(score=80.1),),
        ),
        source="INTELLIGENCE_CYCLE",
    )

    snapshots = repository.list_for_symbol(symbol="AAPL")
    assert first.inserted_count == 1
    assert second.unchanged_count == 1
    assert len(snapshots) == 1
    assert snapshots[0].last_observed_at == NOW + timedelta(minutes=30)


def test_always_records_rank_readiness_and_blocker_changes(tmp_path) -> None:
    repository = OpportunityRankingHistoryRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    repository.record_report(
        report=report(generated_at=NOW, items=(item(),)),
        source="INTELLIGENCE_CYCLE",
    )
    repository.record_report(
        report=report(
            generated_at=NOW + timedelta(minutes=30),
            items=(
                item(
                    rank=2,
                    score=80.05,
                    eligible=True,
                    blockers=(),
                ),
            ),
        ),
        source="INTELLIGENCE_CYCLE",
    )

    snapshots = repository.list_for_symbol(symbol="AAPL")
    assert len(snapshots) == 2
    assert snapshots[-1].rank == 2
    assert snapshots[-1].eligible_for_execution is True
    assert snapshots[-1].blockers == ()


def test_history_explains_score_rank_component_and_blocker_movement(tmp_path) -> None:
    repository = OpportunityRankingHistoryRepository(
        database_path=str(tmp_path / "app.db")
    )
    service = OpportunityRankingHistoryService(
        repository=repository,
        now_provider=lambda: NOW + timedelta(hours=1),
    )
    service.initialize()
    service.capture(
        report=report(generated_at=NOW, items=(item(),)),
        source="INTELLIGENCE_CYCLE",
    )
    service.capture(
        report=report(
            generated_at=NOW + timedelta(minutes=30),
            items=(
                item(
                    rank=1,
                    score=83.0,
                    eligible=True,
                    blockers=(),
                    thesis_value=17.0,
                ),
            ),
        ),
        source="INTELLIGENCE_CYCLE",
    )

    history = service.get_symbol_history(symbol="AAPL", window_days=1)
    change = history.changes[-1]

    assert history.score_change == 3.0
    assert history.snapshot_count == 2
    assert history.streak_direction == "IMPROVING_1"
    assert change.readiness_changed is True
    assert change.blockers_resolved == ("Graduation incomplete.",)
    assert change.component_changes[0]["label"] == "Thesis quality"
    assert change.component_changes[0]["change"] == 2.0


def test_overview_identifies_largest_riser_and_faller(tmp_path) -> None:
    repository = OpportunityRankingHistoryRepository(
        database_path=str(tmp_path / "app.db")
    )
    service = OpportunityRankingHistoryService(
        repository=repository,
        now_provider=lambda: NOW + timedelta(hours=2),
    )
    service.initialize()
    service.capture(
        report=report(
            generated_at=NOW,
            items=(
                item(symbol="AAPL", rank=1, score=80.0),
                item(symbol="LLY", rank=2, score=70.0),
            ),
        ),
        source="INTELLIGENCE_CYCLE",
    )
    service.capture(
        report=report(
            generated_at=NOW + timedelta(hours=1),
            items=(
                item(symbol="AAPL", rank=1, score=84.0),
                item(symbol="LLY", rank=2, score=67.0),
            ),
        ),
        source="INTELLIGENCE_CYCLE",
    )

    overview = service.get_overview(window_days=1)

    assert overview.largest_risers[0].symbol == "AAPL"
    assert overview.largest_risers[0].score_change == 4.0
    assert overview.largest_fallers[0].symbol == "LLY"
    assert overview.largest_fallers[0].score_change == -3.0


def test_records_universe_version_and_warns_across_versions(tmp_path) -> None:
    context = ["KAIRO-U-2-AAA", 2]
    repository = OpportunityRankingHistoryRepository(
        database_path=str(tmp_path / "app.db"),
        universe_context_provider=lambda: (context[0], context[1]),
    )
    service = OpportunityRankingHistoryService(
        repository=repository,
        now_provider=lambda: NOW + timedelta(hours=1),
    )
    service.initialize()
    service.capture(
        report=report(generated_at=NOW, items=(item(),)),
        source="INTELLIGENCE_CYCLE",
    )
    context[:] = ["KAIRO-U-3-BBB", 3]
    service.capture(
        report=report(
            generated_at=NOW + timedelta(minutes=30),
            items=(item(rank=2, score=80.0),),
        ),
        source="INTELLIGENCE_CYCLE",
    )

    history = service.get_symbol_history(symbol="AAPL", window_days=1)

    assert history.snapshots[0].universe_size == 2
    assert history.snapshots[-1].universe_size == 3
    assert history.rank_comparability_warning is not None
