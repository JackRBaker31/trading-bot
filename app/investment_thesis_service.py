from collections.abc import Callable
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from app.investment_capability_providers import (
    SymbolCapabilityProvider,
)
from app.investment_thesis_models import (
    InvestmentThesis,
    InvestmentThesisReport,
    ThesisCapabilityAssessment,
)
from app.intelligence_snapshot import (
    IntelligenceOpportunity,
    IntelligenceSnapshot,
    TradingReadiness,
)
from app.operations_query_service import (
    PortfolioView,
    RiskStatusView,
)


class GraduationStatusLike(
    Protocol,
):
    eligible: bool
    failed_checks: tuple[str, ...]


class InvestmentThesisService:
    def __init__(
        self,
        *,
        snapshot_provider: Callable[
            [],
            IntelligenceSnapshot,
        ],
        risk_provider: Callable[
            [],
            RiskStatusView,
        ],
        portfolio_provider: Callable[
            [],
            PortfolioView,
        ],
        graduation_provider: Callable[
            [],
            GraduationStatusLike,
        ],
        capability_providers: tuple[
            SymbolCapabilityProvider,
            ...
        ],
        now_provider: Callable[
            [],
            datetime,
        ] | None = None,
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
        self._capability_providers = (
            capability_providers
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
    ) -> InvestmentThesisReport:
        generated_at = self._utc_now()
        snapshot = self._snapshot_provider()
        risk = self._risk_provider()
        portfolio = (
            self._portfolio_provider()
        )
        graduation = (
            self._graduation_provider()
        )

        platform_blockers = list(
            snapshot.readiness_reasons
        )
        platform_blockers.extend(
            graduation.failed_checks
        )

        theses = tuple(
            self._build_thesis(
                opportunity=opportunity,
                snapshot=snapshot,
                risk=risk,
                portfolio=portfolio,
                graduation=graduation,
                generated_at=generated_at,
            )
            for opportunity
            in snapshot.top_opportunities
        )

        available_capabilities = {
            assessment.capability
            for thesis in theses
            for assessment
            in thesis.capabilities
            if assessment.status
            == "AVAILABLE"
        }

        return InvestmentThesisReport(
            generated_at=generated_at,
            thesis_count=len(theses),
            executable_count=sum(
                1
                for thesis in theses
                if thesis.eligible_for_execution
            ),
            complete_capability_count=len(
                available_capabilities
            ),
            required_capability_count=len(
                self._capability_providers
            ),
            theses=theses,
            platform_blockers=tuple(
                dict.fromkeys(
                    platform_blockers
                )
            ),
            warnings=tuple(
                snapshot.risk_warnings
            ),
        )

    def _build_thesis(
        self,
        *,
        opportunity: (
            IntelligenceOpportunity
        ),
        snapshot: IntelligenceSnapshot,
        risk: RiskStatusView,
        portfolio: PortfolioView,
        graduation: GraduationStatusLike,
        generated_at: datetime,
    ) -> InvestmentThesis:
        assessments = tuple(
            provider.assess(
                symbol=opportunity.symbol,
                opportunity=opportunity,
                snapshot=snapshot,
                risk=risk,
                portfolio=portfolio,
            )
            for provider
            in self._capability_providers
        )

        available = tuple(
            item
            for item in assessments
            if (
                item.status == "AVAILABLE"
                and item.score is not None
            )
        )

        available_score = sum(
            float(item.score)
            for item in available
        )
        available_maximum = sum(
            item.maximum
            for item in available
        )

        score = (
            round(
                available_score
                / available_maximum
                * 100,
                2,
            )
            if available_maximum > 0
            else 0.0
        )

        confidence_pairs = [
            (
                float(item.confidence),
                item.maximum,
            )
            for item in available
            if item.confidence is not None
        ]

        confidence_weight = sum(
            weight
            for _, weight
            in confidence_pairs
        )

        confidence = (
            round(
                sum(
                    value * weight
                    for value, weight
                    in confidence_pairs
                )
                / confidence_weight,
                4,
            )
            if confidence_weight > 0
            else 0.0
        )

        total_maximum = sum(
            item.maximum
            for item in assessments
        )

        coverage = (
            round(
                available_maximum
                / total_maximum,
                4,
            )
            if total_maximum > 0
            else 0.0
        )

        blockers: list[str] = []

        blockers.extend(
            blocker
            for item in assessments
            for blocker in item.blockers
        )
        blockers.extend(
            opportunity.blocking_reasons
        )
        blockers.extend(
            snapshot.readiness_reasons
        )
        blockers.extend(
            graduation.failed_checks
        )

        missing_required = tuple(
            item.capability
            for item in assessments
            if item.status
            != "AVAILABLE"
        )

        if missing_required:
            blockers.append(
                "Required capabilities are "
                "not yet available: "
                + ", ".join(
                    missing_required
                )
                + "."
            )

        unique_blockers = tuple(
            dict.fromkeys(
                blocker
                for blocker in blockers
                if blocker.strip()
            )
        )

        recommendation = (
            self._recommendation(
                score=score,
                confidence=confidence,
                blocked=bool(
                    unique_blockers
                ),
                sentiment=(
                    opportunity.sentiment
                ),
            )
        )

        eligible = (
            recommendation
            == "BUY_CANDIDATE"
            and not unique_blockers
            and coverage == 1.0
            and graduation.eligible
            and (
                self._value(
                    snapshot
                    .trading_readiness
                )
                == (
                    TradingReadiness
                    .READY
                    .value
                )
            )
        )

        time_horizon = (
            self._time_horizon(
                event_type=(
                    opportunity.event_type
                )
            )
        )

        risk_tier = (
            self._risk_tier(
                confidence=confidence,
                coverage=coverage,
                blockers=(
                    unique_blockers
                ),
            )
        )

        suggested_value = (
            self._position_value(
                score=score,
                confidence=confidence,
                risk_tier=risk_tier,
                eligible=eligible,
                risk=risk,
                portfolio=portfolio,
            )
        )

        primary_driver = (
            max(
                available,
                key=lambda item: (
                    float(item.score)
                    / item.maximum
                ),
            ).capability
            if available
            else "NONE"
        )

        warnings = list(
            snapshot.risk_warnings
        )

        if missing_required:
            warnings.append(
                "This thesis is incomplete "
                "and must not be used for "
                "execution."
            )

        reasons = (
            (
                "Normalised thesis score is "
                f"{score:.2f}/100 across "
                f"{len(available)} available "
                "capability assessment(s)."
            ),
            (
                "Capability coverage is "
                f"{coverage * 100:.1f}%."
            ),
            (
                "Weighted confidence is "
                f"{confidence * 100:.1f}%."
            ),
            *opportunity.reasons,
        )

        return InvestmentThesis(
            thesis_id=str(uuid4()),
            generated_at=generated_at,
            symbol=opportunity.symbol,
            recommendation=recommendation,
            score=score,
            available_score=round(
                available_score,
                2,
            ),
            available_maximum=round(
                available_maximum,
                2,
            ),
            confidence=confidence,
            confidence_coverage=coverage,
            risk_tier=risk_tier,
            time_horizon=time_horizon,
            suggested_position_value=(
                suggested_value
            ),
            eligible_for_execution=eligible,
            headline=opportunity.headline,
            primary_driver=primary_driver,
            capabilities=assessments,
            reasons=tuple(reasons),
            blockers=unique_blockers,
            warnings=tuple(
                dict.fromkeys(
                    warnings
                )
            ),
        )

    @staticmethod
    def _recommendation(
        *,
        score: float,
        confidence: float,
        blocked: bool,
        sentiment: str,
    ) -> str:
        if sentiment.upper().strip() in {
            "NEGATIVE",
            "-1",
            "-1.0",
        }:
            return "AVOID"

        if blocked:
            return "INCOMPLETE"

        if (
            score >= 80
            and confidence >= 0.80
        ):
            return "BUY_CANDIDATE"

        if score >= 65:
            return "WATCH"

        return "MONITOR"

    @staticmethod
    def _time_horizon(
        *,
        event_type: str,
    ) -> str:
        value = event_type.upper()

        if "LONGTERM" in value:
            return "POSITION"

        if "SHORTTERM" in value:
            return "SWING"

        return "UNSPECIFIED"

    @staticmethod
    def _risk_tier(
        *,
        confidence: float,
        coverage: float,
        blockers: tuple[str, ...],
    ) -> str:
        if blockers or coverage < 0.75:
            return "HIGH"

        if (
            confidence >= 0.90
            and coverage == 1.0
        ):
            return "LOW"

        return "MEDIUM"

    @staticmethod
    def _position_value(
        *,
        score: float,
        confidence: float,
        risk_tier: str,
        eligible: bool,
        risk: RiskStatusView,
        portfolio: PortfolioView,
    ) -> float:
        if not eligible:
            return 0.0

        cash = (
            float(portfolio.cash)
            if (
                portfolio.available
                and portfolio.cash
                is not None
            )
            else risk.max_order_value
        )

        cap = min(
            risk.max_order_value,
            risk.max_position_value,
            max(0.0, cash),
        )

        risk_factor = {
            "LOW": 0.75,
            "MEDIUM": 0.50,
            "HIGH": 0.25,
        }[
            risk_tier
        ]

        return round(
            cap
            * (score / 100)
            * confidence
            * risk_factor,
            2,
        )

    def _utc_now(
        self,
    ) -> datetime:
        value = self._now_provider()

        if value.tzinfo is None:
            raise ValueError(
                "Investment thesis clock "
                "must be timezone-aware."
            )

        return value.astimezone(
            timezone.utc
        )

    @staticmethod
    def _value(
        value: object,
    ) -> str:
        return str(
            getattr(
                value,
                "value",
                value,
            )
        ).upper().strip()
