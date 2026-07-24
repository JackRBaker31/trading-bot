from collections.abc import Callable
from datetime import date

from app.backtest_models import HistoricalPriceBar
from app.investment_thesis_models import ThesisCapabilityAssessment
from app.intelligence_snapshot import (
    IntelligenceOpportunity,
    IntelligenceSnapshot,
)
from app.macro_analysis_service import MacroAnalysisService
from app.operations_query_service import PortfolioView, RiskStatusView


HistoricalBarsProvider = Callable[
    [str, int],
    list[HistoricalPriceBar],
]


class MacroCapabilityProvider:
    capability = "MACRO"
    maximum = 10.0

    def __init__(
        self,
        *,
        bars_provider: HistoricalBarsProvider,
        analysis_service: MacroAnalysisService | None = None,
        today_provider: Callable[[], date] | None = None,
        symbols: tuple[str, ...] = ("SPY", "QQQ", "TLT"),
        output_size: int = 260,
        maximum_age_days: int = 7,
    ) -> None:
        if output_size < 200:
            raise ValueError("Macro output size must be at least 200.")
        if maximum_age_days <= 0:
            raise ValueError("Maximum age must be positive.")
        if len(symbols) != 3:
            raise ValueError(
                "Macro provider requires SPY, QQQ and TLT proxies."
            )

        self._bars_provider = bars_provider
        self._analysis_service = analysis_service or MacroAnalysisService()
        self._today_provider = today_provider or date.today
        self._symbols = tuple(symbol.upper().strip() for symbol in symbols)
        self._output_size = output_size
        self._maximum_age_days = maximum_age_days

    def get_analysis(self):
        series = {
            proxy: self._bars_provider(proxy, self._output_size)
            for proxy in self._symbols
        }
        return self._analysis_service.analyse(series=series)

    def assess(
        self,
        *,
        symbol: str,
        opportunity: IntelligenceOpportunity,
        snapshot: IntelligenceSnapshot,
        risk: RiskStatusView,
        portfolio: PortfolioView,
    ) -> ThesisCapabilityAssessment:
        del symbol, opportunity, snapshot, risk, portfolio

        try:
            analysis = self.get_analysis()
        except Exception as error:
            return ThesisCapabilityAssessment(
                capability=self.capability,
                status="UNAVAILABLE",
                score=None,
                maximum=self.maximum,
                confidence=None,
                stance="UNKNOWN",
                summary="Macro regime could not be calculated.",
                evidence=(),
                blockers=(
                    f"Macro market data is unavailable: {error}",
                ),
            )

        age_days = (self._today_provider() - analysis.as_of_date).days
        if age_days > self._maximum_age_days:
            return ThesisCapabilityAssessment(
                capability=self.capability,
                status="STALE",
                score=None,
                maximum=self.maximum,
                confidence=analysis.confidence,
                stance="UNKNOWN",
                summary="Macro market data is stale.",
                evidence=(
                    *analysis.evidence,
                    f"Latest aligned data age: {age_days} day(s).",
                ),
                blockers=(
                    f"Macro market data is {age_days} day(s) old.",
                ),
            )

        return ThesisCapabilityAssessment(
            capability=self.capability,
            status="AVAILABLE",
            score=analysis.score,
            maximum=self.maximum,
            confidence=analysis.confidence,
            stance=analysis.stance,
            summary=(
                "Macro score combines broad-market trend, growth "
                "leadership, rate pressure, volatility and freshness."
            ),
            evidence=(
                *analysis.evidence,
                f"Macro regime: {analysis.regime}.",
                f"Macro confidence: {analysis.confidence * 100:.1f}%.",
            ),
            blockers=(),
        )
