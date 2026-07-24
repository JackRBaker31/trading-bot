from collections.abc import Callable
from datetime import date

from app.backtest_models import (
    HistoricalPriceBar,
)
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
from app.technical_analysis_service import (
    TechnicalAnalysisService,
)


HistoricalBarsProvider = Callable[
    [str, int],
    list[HistoricalPriceBar],
]
TodayProvider = Callable[
    [],
    date,
]


class TechnicalCapabilityProvider:
    capability = "TECHNICAL"
    maximum = 20.0

    def __init__(
        self,
        *,
        bars_provider: (
            HistoricalBarsProvider
        ),
        analysis_service: (
            TechnicalAnalysisService
            | None
        ) = None,
        today_provider: (
            TodayProvider
            | None
        ) = None,
        output_size: int = 260,
        maximum_age_days: int = 7,
    ) -> None:
        if output_size < 200:
            raise ValueError(
                "Technical output size "
                "must be at least 200."
            )

        if maximum_age_days <= 0:
            raise ValueError(
                "Maximum age must be positive."
            )

        self._bars_provider = (
            bars_provider
        )
        self._analysis_service = (
            analysis_service
            or TechnicalAnalysisService()
        )
        self._today_provider = (
            today_provider
            or date.today
        )
        self._output_size = output_size
        self._maximum_age_days = (
            maximum_age_days
        )

    def assess(
        self,
        *,
        symbol: str,
        opportunity: (
            IntelligenceOpportunity
        ),
        snapshot: IntelligenceSnapshot,
        risk: RiskStatusView,
        portfolio: PortfolioView,
    ) -> ThesisCapabilityAssessment:
        del (
            opportunity,
            snapshot,
            risk,
            portfolio,
        )

        try:
            bars = self._bars_provider(
                symbol,
                self._output_size,
            )

            analysis = (
                self._analysis_service
                .analyse(
                    symbol=symbol,
                    bars=bars,
                )
            )
        except Exception as error:
            return ThesisCapabilityAssessment(
                capability=self.capability,
                status="UNAVAILABLE",
                score=None,
                maximum=self.maximum,
                confidence=None,
                stance="UNKNOWN",
                summary=(
                    "Technical analysis could "
                    "not be produced."
                ),
                evidence=(),
                blockers=(
                    (
                        "Technical market data "
                        "is unavailable: "
                        f"{error}"
                    ),
                ),
            )

        age_days = (
            self._today_provider()
            - analysis.as_of_date
        ).days

        if age_days > self._maximum_age_days:
            return ThesisCapabilityAssessment(
                capability=self.capability,
                status="STALE",
                score=None,
                maximum=self.maximum,
                confidence=(
                    analysis.confidence
                ),
                stance="UNKNOWN",
                summary=(
                    "Technical market data "
                    "is stale."
                ),
                evidence=(
                    *analysis.evidence,
                    (
                        "Latest bar age: "
                        f"{age_days} day(s)."
                    ),
                ),
                blockers=(
                    (
                        "Technical market data "
                        f"is {age_days} day(s) "
                        "old."
                    ),
                ),
            )

        return ThesisCapabilityAssessment(
            capability=self.capability,
            status="AVAILABLE",
            score=analysis.score,
            maximum=self.maximum,
            confidence=(
                analysis.confidence
            ),
            stance=analysis.stance,
            summary=(
                "Technical score combines "
                "trend, momentum, volatility, "
                "volume and price structure."
            ),
            evidence=(
                *analysis.evidence,
                (
                    "Technical confidence: "
                    f"{analysis.confidence * 100:.1f}%."
                ),
                (
                    "Latest close: "
                    f"{analysis.latest_close:.4f}."
                ),
            ),
            blockers=(),
        )
