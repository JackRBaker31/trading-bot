from collections.abc import Callable
from datetime import datetime, timezone
from typing import Protocol

from app.decision_engine_models import (
    DecisionIntelligenceReport,
    DecisionScoreComponent,
    InvestmentDecision,
)
from app.intelligence_snapshot import (
    EvidenceQuality,
    IntelligenceOpportunity,
    IntelligenceSnapshot,
    MarketOutlook,
    TradingReadiness,
)
from app.operations_query_service import (
    OperationsQueryRequest,
    PortfolioView,
    RiskStatusView,
)


class GraduationStatusLike(
    Protocol,
):
    eligible: bool
    failed_checks: tuple[str, ...]


SnapshotProvider = Callable[
    [],
    IntelligenceSnapshot,
]
RiskProvider = Callable[
    [],
    RiskStatusView,
]
PortfolioProvider = Callable[
    [],
    PortfolioView,
]
GraduationProvider = Callable[
    [],
    GraduationStatusLike,
]
NowProvider = Callable[
    [],
    datetime,
]


class DecisionEngineService:
    """
    Deterministic investment-decision scoring.

    This service never submits an order. It
    produces an advisory recommendation and
    preserves all existing operational,
    graduation and risk-policy gates.
    """

    def __init__(
        self,
        *,
        snapshot_provider: SnapshotProvider,
        risk_provider: RiskProvider,
        portfolio_provider: (
            PortfolioProvider
        ),
        graduation_provider: (
            GraduationProvider
        ),
        now_provider: (
            NowProvider | None
        ) = None,
    ) -> None:
        self._snapshot_provider = (
            snapshot_provider
        )
        self._risk_provider = (
            risk_provider
        )
        self._portfolio_provider = (
            portfolio_provider
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

    def get_report(
        self,
    ) -> DecisionIntelligenceReport:
        generated_at = self._utc_now()
        snapshot = (
            self._snapshot_provider()
        )
        risk = self._risk_provider()
        portfolio = (
            self._portfolio_provider()
        )
        graduation = (
            self._graduation_provider()
        )

        readiness = self._enum_value(
            snapshot.trading_readiness
        )
        graduation_eligible = bool(
            graduation.eligible
        )

        platform_blockers = list(
            snapshot.readiness_reasons
        )

        platform_blockers.extend(
            graduation.failed_checks
        )

        if not risk.paper_trading_enabled:
            platform_blockers.append(
                "Paper trading is disabled."
            )

        if (
            risk.broker_environment
            .upper()
            != "DEMO"
        ):
            platform_blockers.append(
                "Broker environment is not DEMO."
            )

        if (
            not risk
            .execution_permission_confirmed
        ):
            platform_blockers.append(
                "Order execution permission "
                "has not been confirmed."
            )

        decisions = tuple(
            self._decision(
                opportunity=opportunity,
                snapshot=snapshot,
                risk=risk,
                portfolio=portfolio,
                graduation_eligible=(
                    graduation_eligible
                ),
                graduation_failures=(
                    graduation.failed_checks
                ),
                generated_at=generated_at,
            )
            for opportunity
            in snapshot.top_opportunities
        )

        warnings = tuple(
            dict.fromkeys(
                (
                    *snapshot.risk_warnings,
                    *(
                        (
                            "Portfolio valuation is "
                            "not available; suggested "
                            "position values are "
                            "advisory caps only."
                        ,)
                        if (
                            portfolio.available
                            and not hasattr(
                                portfolio,
                                "total_value",
                            )
                        )
                        else ()
                    ),
                )
            )
        )

        return DecisionIntelligenceReport(
            generated_at=generated_at,
            trading_readiness=readiness,
            graduation_eligible=(
                graduation_eligible
            ),
            decision_count=len(
                decisions
            ),
            executable_candidate_count=sum(
                1
                for decision
                in decisions
                if (
                    decision
                    .eligible_for_execution
                )
            ),
            decisions=decisions,
            platform_blockers=tuple(
                dict.fromkeys(
                    platform_blockers
                )
            ),
            warnings=warnings,
        )

    def _decision(
        self,
        *,
        opportunity: (
            IntelligenceOpportunity
        ),
        snapshot: IntelligenceSnapshot,
        risk: RiskStatusView,
        portfolio: PortfolioView,
        graduation_eligible: bool,
        graduation_failures: tuple[
            str,
            ...
        ],
        generated_at: datetime,
    ) -> InvestmentDecision:
        components = (
            self._score_components(
                opportunity=opportunity,
                snapshot=snapshot,
            )
        )

        score = round(
            max(
                0.0,
                min(
                    100.0,
                    sum(
                        component.value
                        for component
                        in components
                    ),
                ),
            ),
            2,
        )

        blockers = list(
            opportunity
            .blocking_reasons
        )

        readiness = self._enum_value(
            snapshot.trading_readiness
        )

        if (
            readiness
            != TradingReadiness.READY.value
        ):
            blockers.extend(
                snapshot.readiness_reasons
            )

        if not graduation_eligible:
            blockers.extend(
                graduation_failures
            )

        if (
            opportunity.symbol
            not in risk.approved_symbols
        ):
            blockers.append(
                "Symbol is not approved "
                "by the risk policy."
            )

        if not risk.paper_trading_enabled:
            blockers.append(
                "Paper trading is disabled."
            )

        if (
            risk.broker_environment
            .upper()
            != "DEMO"
        ):
            blockers.append(
                "Broker environment is not DEMO."
            )

        if (
            not risk
            .execution_permission_confirmed
        ):
            blockers.append(
                "Order execution permission "
                "has not been confirmed."
            )

        negative_sentiment = (
            opportunity.sentiment
            .upper()
            in {
                "NEGATIVE",
                "-1",
                "-1.0",
            }
        )

        if negative_sentiment:
            blockers.append(
                "The latest selected signal "
                "has negative sentiment."
            )

        unique_blockers = tuple(
            dict.fromkeys(
                blocker
                for blocker in blockers
                if blocker.strip()
            )
        )

        risk_tier = self._risk_tier(
            opportunity=opportunity,
            snapshot=snapshot,
        )

        recommendation = (
            self._recommendation(
                score=score,
                blocked=bool(
                    unique_blockers
                ),
                negative_sentiment=(
                    negative_sentiment
                ),
            )
        )

        eligible = (
            recommendation
            == "BUY_CANDIDATE"
            and not unique_blockers
        )

        suggested_value = (
            self._suggested_position_value(
                score=score,
                confidence=(
                    opportunity.confidence
                ),
                risk_tier=risk_tier,
                risk=risk,
                portfolio=portfolio,
                eligible=eligible,
            )
        )

        warnings = list(
            snapshot.risk_warnings
        )

        if snapshot.freshness.is_stale:
            warnings.extend(
                snapshot
                .freshness
                .stale_reasons
            )

        if (
            self._enum_value(
                snapshot.evidence_quality
            )
            in {
                EvidenceQuality.VERY_LOW.value,
                EvidenceQuality.LOW.value,
            }
        ):
            warnings.append(
                "Historical evidence quality "
                "is still limited."
            )

        reasons = [
            (
                f"Composite decision score "
                f"is {score:.2f}/100."
            ),
            (
                f"Opportunity confidence is "
                f"{opportunity.confidence * 100:.1f}%."
            ),
            *opportunity.reasons,
        ]

        if eligible:
            reasons.append(
                "All deterministic execution "
                "gates passed."
            )
        elif unique_blockers:
            reasons.append(
                f"{len(unique_blockers)} "
                "execution blocker(s) remain."
            )

        return InvestmentDecision(
            symbol=opportunity.symbol,
            generated_at=generated_at,
            recommendation=(
                recommendation
            ),
            score=score,
            confidence=(
                opportunity.confidence
            ),
            risk_tier=risk_tier,
            suggested_position_value=(
                suggested_value
            ),
            eligible_for_execution=(
                eligible
            ),
            headline=opportunity.headline,
            event_type=(
                opportunity.event_type
            ),
            sentiment=(
                opportunity.sentiment
            ),
            classification=(
                self._enum_value(
                    opportunity
                    .classification
                )
            ),
            components=components,
            reasons=tuple(
                dict.fromkeys(
                    reasons
                )
            ),
            blockers=unique_blockers,
            warnings=tuple(
                dict.fromkeys(
                    warning
                    for warning in warnings
                    if warning.strip()
                )
            ),
        )

    def _score_components(
        self,
        *,
        opportunity: (
            IntelligenceOpportunity
        ),
        snapshot: IntelligenceSnapshot,
    ) -> tuple[
        DecisionScoreComponent,
        ...
    ]:
        evidence_value = {
            EvidenceQuality.VERY_LOW.value: 0.0,
            EvidenceQuality.LOW.value: 3.0,
            EvidenceQuality.MODERATE.value: 8.0,
            EvidenceQuality.STRONG.value: 12.0,
        }[
            self._enum_value(
                snapshot.evidence_quality
            )
        ]

        outlook_value = {
            MarketOutlook.PROMISING.value: 8.0,
            MarketOutlook.CAUTIOUS.value: 4.0,
            MarketOutlook.UNFAVOURABLE.value: 0.0,
            MarketOutlook.INSUFFICIENT_DATA.value: 0.0,
        }[
            self._enum_value(
                snapshot.market_outlook
            )
        ]

        freshness_value = (
            0.0
            if snapshot.freshness.is_stale
            else 5.0
        )

        materiality_value = (
            5.0
            if opportunity.is_material
            else 0.0
        )

        confidence_value = round(
            opportunity.confidence
            * 5.0,
            2,
        )

        return (
            DecisionScoreComponent(
                code="OPPORTUNITY",
                label="Opportunity score",
                value=round(
                    opportunity.score
                    * 0.65,
                    2,
                ),
                maximum=65.0,
                detail=(
                    "Weighted news confidence, "
                    "relevance, sentiment and "
                    "materiality."
                ),
            ),
            DecisionScoreComponent(
                code="EVIDENCE",
                label="Evidence quality",
                value=evidence_value,
                maximum=12.0,
                detail=(
                    "Historical news-outcome "
                    "evidence quality is "
                    f"{self._enum_value(snapshot.evidence_quality)}."
                ),
            ),
            DecisionScoreComponent(
                code="OUTLOOK",
                label="Market outlook",
                value=outlook_value,
                maximum=8.0,
                detail=(
                    "Current market outlook is "
                    f"{self._enum_value(snapshot.market_outlook)}."
                ),
            ),
            DecisionScoreComponent(
                code="FRESHNESS",
                label="Research freshness",
                value=freshness_value,
                maximum=5.0,
                detail=(
                    "Research and signal data "
                    "are fresh."
                    if freshness_value
                    else (
                        "Research or signal data "
                        "are stale."
                    )
                ),
            ),
            DecisionScoreComponent(
                code="MATERIALITY",
                label="Material event",
                value=materiality_value,
                maximum=5.0,
                detail=(
                    "The selected event is "
                    "material."
                    if materiality_value
                    else (
                        "The selected event was "
                        "not classified as material."
                    )
                ),
            ),
            DecisionScoreComponent(
                code="CONFIDENCE",
                label="Confidence reinforcement",
                value=confidence_value,
                maximum=5.0,
                detail=(
                    "Additional reinforcement "
                    "from the explainable news "
                    "confidence score."
                ),
            ),
        )

    @staticmethod
    def _recommendation(
        *,
        score: float,
        blocked: bool,
        negative_sentiment: bool,
    ) -> str:
        if negative_sentiment:
            return "AVOID"

        if blocked:
            return "BLOCKED"

        if score >= 80:
            return "BUY_CANDIDATE"

        if score >= 65:
            return "WATCH"

        return "MONITOR"

    def _risk_tier(
        self,
        *,
        opportunity: (
            IntelligenceOpportunity
        ),
        snapshot: IntelligenceSnapshot,
    ) -> str:
        evidence = self._enum_value(
            snapshot.evidence_quality
        )

        if (
            snapshot.freshness.is_stale
            or evidence
            in {
                EvidenceQuality.VERY_LOW.value,
                EvidenceQuality.LOW.value,
            }
            or opportunity.confidence
            < 0.70
        ):
            return "HIGH"

        if (
            evidence
            == EvidenceQuality.STRONG.value
            and opportunity.confidence
            >= 0.90
            and opportunity.is_material
            and not snapshot.risk_warnings
        ):
            return "LOW"

        return "MEDIUM"

    @staticmethod
    def _suggested_position_value(
        *,
        score: float,
        confidence: float,
        risk_tier: str,
        risk: RiskStatusView,
        portfolio: PortfolioView,
        eligible: bool,
    ) -> float:
        if not eligible:
            return 0.0

        available_cash = (
            portfolio.cash
            if (
                portfolio.available
                and portfolio.cash
                is not None
            )
            else risk.max_order_value
        )

        hard_cap = min(
            risk.max_order_value,
            risk.max_position_value,
            max(
                0.0,
                float(
                    available_cash
                ),
            ),
        )

        risk_multiplier = {
            "LOW": 0.75,
            "MEDIUM": 0.50,
            "HIGH": 0.25,
        }[
            risk_tier
        ]

        score_multiplier = max(
            0.0,
            min(
                score / 100.0,
                1.0,
            ),
        )

        confidence_multiplier = max(
            0.0,
            min(
                confidence,
                1.0,
            ),
        )

        return round(
            hard_cap
            * risk_multiplier
            * score_multiplier
            * confidence_multiplier,
            2,
        )

    def _utc_now(
        self,
    ) -> datetime:
        value = self._now_provider()

        if value.tzinfo is None:
            raise ValueError(
                "Decision Engine clock "
                "must be timezone-aware."
            )

        return value.astimezone(
            timezone.utc
        )

    @staticmethod
    def _enum_value(
        value: object,
    ) -> str:
        raw = getattr(
            value,
            "value",
            value,
        )
        return str(
            raw
        ).upper().strip()
