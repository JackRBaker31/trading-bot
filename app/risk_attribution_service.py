from typing import Any, Mapping

from app.adaptive_intelligence_models import (
    RiskAttribution,
    RiskContribution,
)


class RiskAttributionService:
    def analyse(
        self,
        *,
        theses: tuple[
            Mapping[str, Any],
            ...
        ],
        portfolio: Mapping[str, Any],
    ) -> RiskAttribution:
        contributions: list[
            RiskContribution
        ] = []

        incomplete = sum(
            1
            for thesis in theses
            if float(
                thesis.get(
                    "confidence_coverage",
                    0.0,
                )
            ) < 1.0
        )
        if incomplete:
            contributions.append(
                RiskContribution(
                    code="INCOMPLETE_THESES",
                    label="Incomplete capability coverage",
                    contribution=min(
                        incomplete * 12.5,
                        35.0,
                    ),
                    severity="HIGH",
                    detail=(
                        f"{incomplete} thesis/theses lack full "
                        "capability coverage."
                    ),
                )
            )

        blocked = sum(
            len(
                thesis.get(
                    "blockers",
                    (),
                )
            )
            for thesis in theses
        )
        if blocked:
            contributions.append(
                RiskContribution(
                    code="EXECUTION_BLOCKERS",
                    label="Execution blockers",
                    contribution=min(
                        blocked * 5.0,
                        25.0,
                    ),
                    severity="HIGH",
                    detail=(
                        f"{blocked} deterministic blocker(s) "
                        "remain across current theses."
                    ),
                )
            )

        high_risk = sum(
            1
            for thesis in theses
            if str(
                thesis.get(
                    "risk_tier",
                    "",
                )
            )
            == "HIGH"
        )
        if high_risk:
            contributions.append(
                RiskContribution(
                    code="HIGH_RISK_THESES",
                    label="High-risk theses",
                    contribution=min(
                        high_risk * 10.0,
                        25.0,
                    ),
                    severity="MEDIUM",
                    detail=(
                        f"{high_risk} current thesis/theses "
                        "are classified HIGH risk."
                    ),
                )
            )

        cash = portfolio.get("cash")
        starting_cash = portfolio.get(
            "starting_cash"
        )
        if (
            cash is not None
            and starting_cash
            not in (None, 0)
        ):
            cash_ratio = (
                float(cash)
                / float(starting_cash)
            )
            if cash_ratio < 0.20:
                contributions.append(
                    RiskContribution(
                        code="LOW_CASH_BUFFER",
                        label="Low cash buffer",
                        contribution=20.0,
                        severity="HIGH",
                        detail=(
                            f"Cash is {cash_ratio * 100:.1f}% "
                            "of starting capital."
                        ),
                    )
                )

        total = round(
            min(
                sum(
                    item.contribution
                    for item in contributions
                ),
                100.0,
            ),
            2,
        )

        tier = (
            "CRITICAL"
            if total >= 75
            else "HIGH"
            if total >= 50
            else "MEDIUM"
            if total >= 25
            else "LOW"
        )

        dominant = (
            max(
                contributions,
                key=lambda item: (
                    item.contribution
                ),
            ).code
            if contributions
            else None
        )

        return RiskAttribution(
            overall_risk_score=total,
            overall_tier=tier,
            contributions=tuple(
                sorted(
                    contributions,
                    key=lambda item: (
                        item.contribution
                    ),
                    reverse=True,
                )
            ),
            dominant_risk=dominant,
            warnings=(
                ()
                if contributions
                else (
                    "No material attributed risk was found "
                    "in the available snapshot.",
                )
            ),
        )
