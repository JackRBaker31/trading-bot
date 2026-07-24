from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Mapping

from app.adaptive_intelligence_models import (
    AdaptiveIntelligenceReport,
)
from app.investment_committee_service import (
    InvestmentCommitteeService,
)
from app.performance_intelligence_service import (
    PerformanceIntelligenceService,
)
from app.portfolio_optimisation_service import (
    PortfolioOptimisationService,
)
from app.position_sizing_service import (
    PositionSizingService,
)
from app.risk_attribution_service import (
    RiskAttributionService,
)
from app.strategy_evolution_service import (
    StrategyEvolutionService,
)


class AdaptiveIntelligenceService:
    def __init__(
        self,
        *,
        decisions_provider: Callable[
            [],
            tuple[
                Mapping[str, Any],
                ...
            ],
        ],
        outcomes_provider: Callable[
            [],
            tuple[
                Mapping[str, Any],
                ...
            ],
        ],
        theses_provider: Callable[
            [],
            tuple[
                Mapping[str, Any],
                ...
            ],
        ],
        portfolio_provider: Callable[
            [],
            Mapping[str, Any],
        ],
        risk_provider: Callable[
            [],
            Mapping[str, Any],
        ],
        performance_service: (
            PerformanceIntelligenceService
        ),
        portfolio_service: (
            PortfolioOptimisationService
        ),
        risk_service: (
            RiskAttributionService
        ),
        sizing_service: (
            PositionSizingService
        ),
        committee_service: (
            InvestmentCommitteeService
        ),
        evolution_service: (
            StrategyEvolutionService
        ),
    ) -> None:
        self._decisions_provider = decisions_provider
        self._outcomes_provider = outcomes_provider
        self._theses_provider = theses_provider
        self._portfolio_provider = portfolio_provider
        self._risk_provider = risk_provider
        self._performance_service = performance_service
        self._portfolio_service = portfolio_service
        self._risk_service = risk_service
        self._sizing_service = sizing_service
        self._committee_service = committee_service
        self._evolution_service = evolution_service

    def report(
        self,
    ) -> AdaptiveIntelligenceReport:
        decisions = self._decisions_provider()
        outcomes = self._outcomes_provider()
        theses = self._theses_provider()
        portfolio = self._portfolio_provider()
        risk = self._risk_provider()

        performance = (
            self._performance_service
            .analyse(
                decisions=decisions,
                outcomes=outcomes,
            )
        )

        available_cash = float(
            portfolio.get(
                "cash",
                0.0,
            )
            or 0.0
        )

        portfolio_result = (
            self._portfolio_service
            .optimise(
                theses=theses,
                available_cash=available_cash,
                maximum_portfolio_exposure_ratio=float(
                    risk.get(
                        "max_portfolio_exposure_ratio",
                        0.0,
                    )
                    or 0.0
                ),
            )
        )

        risk_result = (
            self._risk_service
            .analyse(
                theses=theses,
                portfolio=portfolio,
            )
        )

        position_sizes = (
            self._sizing_service
            .recommend(
                theses=theses,
                performance=performance,
                maximum_order_value=float(
                    risk.get(
                        "max_order_value",
                        0.0,
                    )
                    or 0.0
                ),
                maximum_position_value=float(
                    risk.get(
                        "max_position_value",
                        0.0,
                    )
                    or 0.0
                ),
                available_cash=available_cash,
            )
        )

        committee = (
            self._committee_service
            .deliberate(
                theses=theses
            )
        )

        return AdaptiveIntelligenceReport(
            generated_at=datetime.now(
                timezone.utc
            ),
            performance=performance,
            portfolio=portfolio_result,
            risk=risk_result,
            position_sizes=position_sizes,
            committee=committee,
            proposals=(
                self._evolution_service
                .recent()
            ),
            execution_mode=(
                "ADVISORY_ONLY"
            ),
            warnings=(
                "No service in this bundle submits orders.",
                "Strategy evolution proposals require manual review.",
                "Learning confidence remains low until adequate "
                "outcome samples exist.",
            ),
        )

    def propose_evolution(
        self,
    ):
        performance = (
            self._performance_service
            .analyse(
                decisions=(
                    self._decisions_provider()
                ),
                outcomes=(
                    self._outcomes_provider()
                ),
            )
        )
        return self._evolution_service.propose(
            performance=performance
        )
