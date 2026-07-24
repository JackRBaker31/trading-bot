from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Mapping

from app.advanced_intelligence_models import (
    AdvancedIntelligenceReport,
)
from app.bayesian_confidence_service import (
    BayesianConfidenceService,
)
from app.explainable_decision_service import (
    ExplainableDecisionService,
)
from app.market_regime_service import (
    MarketRegimeService,
)
from app.multi_timeframe_service import (
    MultiTimeframeService,
)


class AdvancedIntelligenceService:
    def __init__(
        self,
        *,
        regime_series_provider: Callable[
            [],
            Mapping[str, Any],
        ],
        timeframe_series_provider: Callable[
            [str],
            Mapping[str, Any],
        ],
        theses_provider: Callable[
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
        regime_service: MarketRegimeService,
        timeframe_service: MultiTimeframeService,
        calibration_service: BayesianConfidenceService,
        explanation_service: ExplainableDecisionService,
    ) -> None:
        self._regime_series_provider = (
            regime_series_provider
        )
        self._timeframe_series_provider = (
            timeframe_series_provider
        )
        self._theses_provider = theses_provider
        self._outcomes_provider = outcomes_provider
        self._regime_service = regime_service
        self._timeframe_service = timeframe_service
        self._calibration_service = (
            calibration_service
        )
        self._explanation_service = (
            explanation_service
        )

    def report(
        self,
    ) -> AdvancedIntelligenceReport:
        theses = self._theses_provider()
        regime = self._regime_service.analyse(
            series=self._regime_series_provider()
        )
        calibration = (
            self._calibration_service
            .calibrate(
                outcomes=self._outcomes_provider()
            )
        )

        timeframe_results = []
        timeframe_by_symbol = {}

        for thesis in theses:
            symbol = str(thesis["symbol"])
            try:
                result = (
                    self._timeframe_service
                    .analyse(
                        symbol=symbol,
                        series=(
                            self
                            ._timeframe_series_provider(
                                symbol
                            )
                        ),
                    )
                )
            except Exception:
                continue

            timeframe_results.append(result)
            timeframe_by_symbol[symbol] = result

        decisions = (
            self._explanation_service
            .explain(
                theses=theses,
                regime=regime,
                timeframe_by_symbol=(
                    timeframe_by_symbol
                ),
                calibration=calibration,
            )
        )

        return AdvancedIntelligenceReport(
            generated_at=datetime.now(
                timezone.utc
            ),
            execution_mode="ADVISORY_ONLY",
            regime=regime,
            multi_timeframe=tuple(
                timeframe_results
            ),
            decisions=decisions,
            calibration=calibration,
            warnings=(
                "No order submission occurs in this service.",
                "Bayesian calibration is conservative when "
                "sample counts are low.",
                "Missing intraday timeframes reduce confidence "
                "rather than being fabricated.",
            ),
        )
