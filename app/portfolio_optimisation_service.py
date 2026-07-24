from typing import Any, Mapping

from app.adaptive_intelligence_models import (
    PortfolioAllocation,
    PortfolioOptimisation,
)


class PortfolioOptimisationService:
    def optimise(
        self,
        *,
        theses: tuple[
            Mapping[str, Any],
            ...
        ],
        available_cash: float,
        maximum_portfolio_exposure_ratio: float,
        maximum_symbol_weight: float = 0.25,
    ) -> PortfolioOptimisation:
        investable_cash = max(
            0.0,
            available_cash
            * maximum_portfolio_exposure_ratio,
        )

        candidates = [
            thesis
            for thesis in theses
            if (
                bool(
                    thesis.get(
                        "eligible_for_execution",
                        False,
                    )
                )
                and str(
                    thesis.get(
                        "recommendation",
                        "",
                    )
                )
                == "BUY_CANDIDATE"
            )
        ]

        raw_scores = [
            max(
                0.0,
                float(thesis["score"])
                * float(thesis["confidence"])
                * self._risk_multiplier(
                    str(
                        thesis["risk_tier"]
                    )
                ),
            )
            for thesis in candidates
        ]

        total_raw = sum(raw_scores)
        allocations: list[
            PortfolioAllocation
        ] = []

        remaining = 1.0

        for thesis, raw_score in sorted(
            zip(
                candidates,
                raw_scores,
                strict=True,
            ),
            key=lambda item: item[1],
            reverse=True,
        ):
            raw_weight = (
                raw_score / total_raw
                if total_raw > 0
                else 0.0
            )
            constrained = min(
                raw_weight,
                maximum_symbol_weight,
                remaining,
            )
            remaining = max(
                0.0,
                remaining - constrained,
            )

            allocations.append(
                PortfolioAllocation(
                    symbol=str(
                        thesis["symbol"]
                    ),
                    recommendation=str(
                        thesis["recommendation"]
                    ),
                    raw_weight=round(
                        raw_weight,
                        6,
                    ),
                    constrained_weight=round(
                        constrained,
                        6,
                    ),
                    suggested_value=round(
                        investable_cash
                        * constrained,
                        2,
                    ),
                    score=float(
                        thesis["score"]
                    ),
                    confidence=float(
                        thesis["confidence"]
                    ),
                    risk_tier=str(
                        thesis["risk_tier"]
                    ),
                    reasons=(
                        "Weighted by thesis score, confidence "
                        "and risk tier.",
                        "Capped by the maximum symbol weight.",
                    ),
                )
            )

        allocated = sum(
            item.suggested_value
            for item in allocations
        )

        warnings = (
            (
                "No complete executable BUY candidates are "
                "currently available.",
            )
            if not allocations
            else ()
        )

        return PortfolioOptimisation(
            available_cash=round(
                available_cash,
                2,
            ),
            investable_cash=round(
                investable_cash,
                2,
            ),
            maximum_symbol_weight=(
                maximum_symbol_weight
            ),
            allocations=tuple(allocations),
            unallocated_cash=round(
                max(
                    investable_cash - allocated,
                    0.0,
                ),
                2,
            ),
            warnings=warnings,
        )

    @staticmethod
    def _risk_multiplier(
        risk_tier: str,
    ) -> float:
        return {
            "LOW": 1.0,
            "MEDIUM": 0.75,
            "HIGH": 0.40,
        }.get(
            risk_tier.upper(),
            0.40,
        )
