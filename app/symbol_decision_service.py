from collections.abc import Callable
from datetime import datetime, timezone
from uuid import uuid4

from app.intelligence_graduation import (
    IntelligenceGraduationStatus,
)
from app.intelligence_snapshot import (
    IntelligenceOpportunity,
    IntelligenceSnapshot,
    TradingReadiness,
)
from app.symbol_decision_models import (
    SymbolDecisionStage,
    SymbolDecisionTrace,
)
from app.symbol_decision_repository import (
    SymbolDecisionRepository,
)


SnapshotProvider = Callable[
    [],
    IntelligenceSnapshot,
]
GraduationProvider = Callable[
    [],
    IntelligenceGraduationStatus,
]
NowProvider = Callable[
    [],
    datetime,
]


class SymbolDecisionService:
    def __init__(
        self,
        *,
        repository: SymbolDecisionRepository,
        snapshot_provider: SnapshotProvider,
        graduation_provider: GraduationProvider,
        now_provider: NowProvider | None = None,
    ) -> None:
        self._repository = repository
        self._snapshot_provider = (
            snapshot_provider
        )
        self._graduation_provider = (
            graduation_provider
        )
        self._now_provider = (
            now_provider
            or (
                lambda: datetime.now(
                    timezone.utc
                )
            )
        )

    def initialize(self) -> None:
        self._repository.initialize()

    def capture_current(
        self,
    ) -> tuple[
        SymbolDecisionTrace,
        ...
    ]:
        snapshot = self._snapshot_provider()
        graduation = (
            self._graduation_provider()
        )

        traces = tuple(
            self._build_trace(
                opportunity=opportunity,
                snapshot=snapshot,
                graduation=graduation,
            )
            for opportunity
            in snapshot.top_opportunities
        )

        for trace in traces:
            self._repository.save(
                trace=trace
            )

        return traces

    def list_current(
        self,
    ) -> tuple[
        SymbolDecisionTrace,
        ...
    ]:
        return self.capture_current()

    def get_current(
        self,
        *,
        symbol: str,
    ) -> SymbolDecisionTrace | None:
        cleaned_symbol = (
            symbol.upper().strip()
        )

        for trace in self.capture_current():
            if trace.symbol == cleaned_symbol:
                return trace

        return None

    def list_history(
        self,
        *,
        symbol: str | None = None,
        limit: int = 100,
        capture_current: bool = True,
    ) -> tuple[
        SymbolDecisionTrace,
        ...
    ]:
        if capture_current:
            self.capture_current()

        return self._repository.list_recent(
            limit=limit,
            symbol=symbol,
        )

    def _build_trace(
        self,
        *,
        opportunity: IntelligenceOpportunity,
        snapshot: IntelligenceSnapshot,
        graduation: IntelligenceGraduationStatus,
    ) -> SymbolDecisionTrace:
        blockers = tuple(
            dict.fromkeys(
                (
                    *opportunity.blocking_reasons,
                    *(
                        ()
                        if graduation.eligible
                        else graduation.failed_checks
                    ),
                )
            )
        )

        trade_candidate = (
            opportunity.eligible_for_trade
            and snapshot.trading_readiness
            is TradingReadiness.READY
            and graduation.eligible
        )

        decision = (
            "TRADE_CANDIDATE"
            if trade_candidate
            else "BLOCKED"
        )

        score_evidence = tuple(
            f"{name.replace('_', ' ').title()}: "
            f"{value:.2f} points."
            for name, value
            in sorted(
                opportunity
                .score_breakdown
                .items()
            )
        )

        stages = (
            SymbolDecisionStage(
                sequence=1,
                stage="RESEARCH",
                status=(
                    "PASS"
                    if opportunity.is_material
                    else "REVIEW"
                ),
                title="Research Evidence",
                summary=opportunity.headline,
                evidence=(
                    (
                        "Event type: "
                        f"{opportunity.event_type}."
                    ),
                    (
                        "Published at: "
                        f"{opportunity.published_at}."
                    ),
                    (
                        "Material event: "
                        f"{'Yes' if opportunity.is_material else 'No'}."
                    ),
                ),
            ),
            SymbolDecisionStage(
                sequence=2,
                stage="SENTIMENT",
                status=(
                    "PASS"
                    if opportunity.confidence >= 0.80
                    else "REVIEW"
                ),
                title="News Sentiment",
                summary=(
                    f"Sentiment is "
                    f"{opportunity.sentiment} "
                    f"with "
                    f"{opportunity.confidence * 100:.1f}% "
                    "confidence."
                ),
                evidence=opportunity.reasons,
            ),
            SymbolDecisionStage(
                sequence=3,
                stage="SCORING",
                status=(
                    "PASS"
                    if opportunity.score >= 65
                    else "REVIEW"
                ),
                title="Opportunity Scoring",
                summary=(
                    f"Ranked #{opportunity.rank} "
                    f"with a score of "
                    f"{opportunity.score:.2f} "
                    f"and classification "
                    f"{opportunity.classification.value}."
                ),
                evidence=score_evidence,
            ),
            SymbolDecisionStage(
                sequence=4,
                stage="ELIGIBILITY",
                status=(
                    "PASS"
                    if opportunity.eligible_for_trade
                    else "BLOCKED"
                ),
                title="Risk-Policy Eligibility",
                summary=(
                    "The opportunity passed the "
                    "current eligibility policy."
                    if opportunity.eligible_for_trade
                    else (
                        "The opportunity is blocked "
                        "by current eligibility policy."
                    )
                ),
                evidence=(
                    opportunity.blocking_reasons
                    if opportunity.blocking_reasons
                    else (
                        "No opportunity-level "
                        "blocking reason was recorded.",
                    )
                ),
            ),
            SymbolDecisionStage(
                sequence=5,
                stage="PLATFORM",
                status=(
                    "PASS"
                    if (
                        snapshot.trading_readiness
                        is TradingReadiness.READY
                        and graduation.eligible
                    )
                    else "BLOCKED"
                ),
                title="Platform and Graduation Gates",
                summary=(
                    "Trading readiness is "
                    f"{snapshot.trading_readiness.value}; "
                    "graduation status is "
                    f"{graduation.status}."
                ),
                evidence=tuple(
                    dict.fromkeys(
                        (
                            *snapshot.readiness_reasons,
                            *graduation.failed_checks,
                            *snapshot.risk_warnings,
                        )
                    )
                ),
            ),
            SymbolDecisionStage(
                sequence=6,
                stage="DECISION",
                status=(
                    "PASS"
                    if trade_candidate
                    else "BLOCKED"
                ),
                title="Final Symbol Decision",
                summary=(
                    f"{opportunity.symbol} is a "
                    "trade candidate for further "
                    "order construction and live "
                    "risk evaluation."
                    if trade_candidate
                    else (
                        f"KAIRO withheld "
                        f"{opportunity.symbol} from "
                        "trade-candidate status."
                    )
                ),
                evidence=(
                    blockers
                    if blockers
                    else (
                        "No deterministic symbol "
                        "blocker was recorded.",
                    )
                ),
            ),
        )

        summary = (
            f"{opportunity.symbol} is ranked "
            f"#{opportunity.rank} with a score "
            f"of {opportunity.score:.2f}. "
            + (
                "It currently qualifies as a "
                "trade candidate."
                if trade_candidate
                else (
                    f"It remains blocked by "
                    f"{len(blockers)} recorded "
                    "condition(s)."
                )
            )
        )

        return SymbolDecisionTrace(
            trace_id=str(uuid4()),
            captured_at=self._utc_now(),
            symbol=opportunity.symbol,
            rank=opportunity.rank,
            decision=decision,
            classification=(
                opportunity
                .classification
                .value
            ),
            score=opportunity.score,
            confidence=opportunity.confidence,
            headline=opportunity.headline,
            event_type=opportunity.event_type,
            sentiment=opportunity.sentiment,
            eligible_for_trade=(
                opportunity.eligible_for_trade
            ),
            trading_readiness=(
                snapshot
                .trading_readiness
                .value
            ),
            graduation_ready=(
                graduation.eligible
            ),
            summary=summary,
            stages=stages,
            blockers=blockers,
        )

    def _utc_now(
        self,
    ) -> datetime:
        value = self._now_provider()

        if value.tzinfo is None:
            raise ValueError(
                "Symbol Decision clock must "
                "be timezone-aware."
            )

        return value.astimezone(
            timezone.utc
        )
