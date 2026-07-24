from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from app.investment_thesis_models import (
    ThesisCapabilityAssessment,
)
from app.intelligence_snapshot import (
    IntelligenceOpportunity,
    IntelligenceSnapshot,
)
from app.operations_query_service import (
    PortfolioView,
    RiskStatusView,
)


class SymbolCapabilityProvider(
    Protocol,
):
    capability: str
    maximum: float

    def assess(
        self,
        *,
        symbol: str,
        opportunity: IntelligenceOpportunity,
        snapshot: IntelligenceSnapshot,
        risk: RiskStatusView,
        portfolio: PortfolioView,
    ) -> ThesisCapabilityAssessment:
        ...


@dataclass(frozen=True)
class UnavailableCapabilityProvider:
    capability: str
    maximum: float
    summary: str

    def assess(
        self,
        *,
        symbol: str,
        opportunity: IntelligenceOpportunity,
        snapshot: IntelligenceSnapshot,
        risk: RiskStatusView,
        portfolio: PortfolioView,
    ) -> ThesisCapabilityAssessment:
        del (
            symbol,
            opportunity,
            snapshot,
            risk,
            portfolio,
        )

        return ThesisCapabilityAssessment(
            capability=self.capability,
            status="UNAVAILABLE",
            score=None,
            maximum=self.maximum,
            confidence=None,
            stance="UNKNOWN",
            summary=self.summary,
            evidence=(),
            blockers=(),
        )


@dataclass(frozen=True)
class NewsCapabilityProvider:
    capability: str = "NEWS"
    maximum: float = 25.0

    def assess(
        self,
        *,
        symbol: str,
        opportunity: IntelligenceOpportunity,
        snapshot: IntelligenceSnapshot,
        risk: RiskStatusView,
        portfolio: PortfolioView,
    ) -> ThesisCapabilityAssessment:
        del (
            symbol,
            snapshot,
            risk,
            portfolio,
        )

        score = round(
            min(
                self.maximum,
                max(
                    0.0,
                    (
                        opportunity.score
                        / 100.0
                    )
                    * self.maximum,
                ),
            ),
            2,
        )

        sentiment = (
            opportunity.sentiment
            .upper()
            .strip()
        )

        stance = (
            "BULLISH"
            if sentiment
            in {
                "POSITIVE",
                "1",
                "1.0",
            }
            else "BEARISH"
            if sentiment
            in {
                "NEGATIVE",
                "-1",
                "-1.0",
            }
            else "NEUTRAL"
        )

        return ThesisCapabilityAssessment(
            capability=self.capability,
            status="AVAILABLE",
            score=score,
            maximum=self.maximum,
            confidence=(
                opportunity.confidence
            ),
            stance=stance,
            summary=(
                "Grounded in the current "
                "ranked news opportunity."
            ),
            evidence=(
                opportunity.headline,
                (
                    "Event type: "
                    f"{opportunity.event_type}"
                ),
                (
                    "Opportunity score: "
                    f"{opportunity.score:.2f}"
                ),
                *opportunity.reasons,
            ),
            blockers=(
                opportunity.blocking_reasons
            ),
        )


@dataclass(frozen=True)
class PortfolioCapabilityProvider:
    capability: str = "PORTFOLIO"
    maximum: float = 10.0

    def assess(
        self,
        *,
        symbol: str,
        opportunity: IntelligenceOpportunity,
        snapshot: IntelligenceSnapshot,
        risk: RiskStatusView,
        portfolio: PortfolioView,
    ) -> ThesisCapabilityAssessment:
        del (
            opportunity,
            snapshot,
        )

        if not portfolio.available:
            return ThesisCapabilityAssessment(
                capability=self.capability,
                status="UNAVAILABLE",
                score=None,
                maximum=self.maximum,
                confidence=None,
                stance="UNKNOWN",
                summary=(
                    "Portfolio data is not "
                    "currently available."
                ),
                evidence=(),
                blockers=(),
            )

        approved = (
            symbol in risk.approved_symbols
        )
        has_cash = (
            portfolio.cash is not None
            and portfolio.cash > 0
        )

        score = (
            self.maximum
            if approved and has_cash
            else self.maximum * 0.4
            if approved
            else 0.0
        )

        blockers = (
            ()
            if approved
            else (
                "Symbol is not approved "
                "by the risk policy.",
            )
        )

        return ThesisCapabilityAssessment(
            capability=self.capability,
            status="AVAILABLE",
            score=round(score, 2),
            maximum=self.maximum,
            confidence=1.0,
            stance=(
                "SUPPORTIVE"
                if approved and has_cash
                else "CONSTRAINED"
            ),
            summary=(
                "Assesses approved-symbol "
                "eligibility and available "
                "portfolio cash."
            ),
            evidence=(
                (
                    "Approved symbol: "
                    f"{approved}"
                ),
                (
                    "Available cash: "
                    f"{portfolio.cash}"
                ),
                (
                    "Current positions: "
                    f"{portfolio.position_count}"
                ),
            ),
            blockers=blockers,
        )


@dataclass(frozen=True)
class RiskCapabilityProvider:
    capability: str = "RISK"
    maximum: float = 15.0

    def assess(
        self,
        *,
        symbol: str,
        opportunity: IntelligenceOpportunity,
        snapshot: IntelligenceSnapshot,
        risk: RiskStatusView,
        portfolio: PortfolioView,
    ) -> ThesisCapabilityAssessment:
        del (
            opportunity,
            snapshot,
            portfolio,
        )

        checks = {
            "approved_symbol": (
                symbol in risk.approved_symbols
            ),
            "paper_trading_enabled": (
                risk.paper_trading_enabled
            ),
            "demo_environment": (
                risk.broker_environment
                .upper()
                == "DEMO"
            ),
            "execution_permission": (
                risk
                .execution_permission_confirmed
            ),
            "real_money_disabled": (
                not risk
                .real_money_trading_enabled
            ),
        }

        passed = sum(
            1
            for value in checks.values()
            if value
        )

        score = (
            passed
            / len(checks)
            * self.maximum
        )

        blockers: list[str] = []

        if not checks["approved_symbol"]:
            blockers.append(
                "Symbol is not approved."
            )

        if not checks[
            "paper_trading_enabled"
        ]:
            blockers.append(
                "Paper trading is disabled."
            )

        if not checks[
            "demo_environment"
        ]:
            blockers.append(
                "Broker environment is not DEMO."
            )

        if not checks[
            "execution_permission"
        ]:
            blockers.append(
                "Execution permission has "
                "not been confirmed."
            )

        if not checks[
            "real_money_disabled"
        ]:
            blockers.append(
                "Real-money trading must "
                "remain disabled."
            )

        return ThesisCapabilityAssessment(
            capability=self.capability,
            status="AVAILABLE",
            score=round(score, 2),
            maximum=self.maximum,
            confidence=1.0,
            stance=(
                "PASS"
                if not blockers
                else "BLOCKED"
            ),
            summary=(
                f"{passed} of "
                f"{len(checks)} "
                "deterministic risk checks "
                "passed."
            ),
            evidence=tuple(
                f"{name}: {value}"
                for name, value
                in checks.items()
            ),
            blockers=tuple(blockers),
        )
