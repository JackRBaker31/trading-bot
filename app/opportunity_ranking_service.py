from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from app.historical_similarity_models import HistoricalSimilarityReport
from app.investment_thesis_models import (
    InvestmentThesis,
    InvestmentThesisReport,
    ThesisCapabilityAssessment,
)
from app.opportunity_ranking_history_service import (
    OpportunityRankingHistoryService,
)
from app.opportunity_ranking_models import (
    OpportunityRankingComponent,
    OpportunityRankingReport,
    RankedOpportunity,
)


ThesisReportProvider = Callable[[], InvestmentThesisReport]
SimilarityProvider = Callable[[InvestmentThesis], HistoricalSimilarityReport]
PerformanceReviewProvider = Callable[[], Mapping[str, Any]]
MarketHealthProvider = Callable[[], Mapping[str, Any]]
NowProvider = Callable[[], datetime]


class OpportunityRankingService:
    """Advisory ranking across evidence, performance and readiness signals."""

    METHODOLOGY_VERSION = "KAIRO-ORANK-1.0"
    METHODOLOGY_SUMMARY = (
        "Advisory-only composite ranking using thesis quality, calibrated "
        "confidence, capability coverage, technical and macro alignment, "
        "historical similarity, expected return, measured symbol and sector "
        "performance, risk, execution readiness and market-data health."
    )
    PERFORMANCE_WINDOW_DAYS = 90
    WEIGHTS = {
        "THESIS_QUALITY": 18.0,
        "CALIBRATED_CONFIDENCE": 18.0,
        "EVIDENCE_COVERAGE": 12.0,
        "TECHNICAL_MACRO": 15.0,
        "HISTORICAL_SIMILARITY": 12.0,
        "EXPECTED_RETURN": 10.0,
        "SYMBOL_SECTOR_HISTORY": 6.0,
        "RISK": 4.0,
        "EXECUTION_READINESS": 3.0,
        "DATA_FRESHNESS": 2.0,
    }

    def __init__(
        self,
        *,
        thesis_report_provider: ThesisReportProvider,
        similarity_provider: SimilarityProvider,
        performance_review_provider: PerformanceReviewProvider,
        market_health_provider: MarketHealthProvider,
        history_service: OpportunityRankingHistoryService | None = None,
        now_provider: NowProvider | None = None,
    ) -> None:
        self._thesis_report_provider = thesis_report_provider
        self._similarity_provider = similarity_provider
        self._performance_review_provider = performance_review_provider
        self._market_health_provider = market_health_provider
        self._history_service = history_service
        self._now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )

    def get_report(
        self,
        *,
        capture_source: str = "REPORT",
    ) -> OpportunityRankingReport:
        generated_at = self._utc_now()
        thesis_report = self._thesis_report_provider()
        performance = dict(self._performance_review_provider())
        market_health = dict(self._market_health_provider())

        symbol_analytics = {
            str(item.get("symbol", "")).upper(): item
            for item in performance.get("symbol_analytics", [])
            if isinstance(item, Mapping)
        }
        sector_analytics = {
            str(item.get("sector", "")): item
            for item in performance.get("sector_analytics", [])
            if isinstance(item, Mapping)
        }
        calibration = performance.get("confidence_calibration", {})
        if not isinstance(calibration, Mapping):
            calibration = {}

        drafts: list[RankedOpportunity] = []
        report_warnings: list[str] = list(thesis_report.warnings)

        for thesis in thesis_report.theses:
            similarity: HistoricalSimilarityReport | None = None
            try:
                similarity = self._similarity_provider(thesis)
            except (LookupError, ValueError) as error:
                report_warnings.append(
                    f"Historical similarity was unavailable for "
                    f"{thesis.symbol}: {error}"
                )
            except Exception as error:  # isolate one symbol from the ranking
                report_warnings.append(
                    f"Historical similarity failed for {thesis.symbol}: "
                    f"{type(error).__name__}: {error}"
                )

            symbol_history = symbol_analytics.get(thesis.symbol, {})
            sector = str(symbol_history.get("sector", "Other"))
            sector_history = sector_analytics.get(sector, {})

            drafts.append(
                self._ranked_item(
                    thesis=thesis,
                    similarity=similarity,
                    calibration=calibration,
                    symbol_history=symbol_history,
                    sector_history=sector_history,
                    sector=sector,
                    market_health=market_health,
                    generated_at=generated_at,
                )
            )

        drafts.sort(
            key=lambda item: (
                item.opportunity_score,
                item.eligible_for_execution,
                item.calibrated_confidence,
                item.thesis_score,
                item.symbol,
            ),
            reverse=True,
        )

        ranked = tuple(
            replace(item, rank=index)
            for index, item in enumerate(drafts, start=1)
        )

        report = OpportunityRankingReport(
            generated_at=generated_at,
            methodology_version=self.METHODOLOGY_VERSION,
            methodology_summary=self.METHODOLOGY_SUMMARY,
            advisory_only=True,
            performance_window_days=self.PERFORMANCE_WINDOW_DAYS,
            ranking_count=len(ranked),
            execution_ready_count=sum(
                1 for item in ranked if item.eligible_for_execution
            ),
            high_potential_blocked_count=sum(
                1
                for item in ranked
                if item.category == "HIGH_POTENTIAL_BLOCKED"
            ),
            market_data_status=str(
                market_health.get("status", "UNKNOWN")
            ).upper(),
            component_weights=dict(self.WEIGHTS),
            items=ranked,
            warnings=tuple(dict.fromkeys(report_warnings)),
        )

        if self._history_service is not None:
            try:
                self._history_service.capture(
                    report=report,
                    source=capture_source,
                )
            except Exception as error:
                report = replace(
                    report,
                    warnings=tuple(
                        dict.fromkeys(
                            (
                                *report.warnings,
                                "Opportunity history could not be recorded: "
                                f"{type(error).__name__}: {error}",
                            )
                        )
                    ),
                )

        return report

    def get_history_overview(
        self,
        *,
        window_days: int = 1,
    ):
        if self._history_service is None:
            raise RuntimeError("Opportunity history is not configured.")
        return self._history_service.get_overview(
            window_days=window_days
        )

    def get_symbol_history(
        self,
        *,
        symbol: str,
        window_days: int = 7,
    ):
        if self._history_service is None:
            raise RuntimeError("Opportunity history is not configured.")
        return self._history_service.get_symbol_history(
            symbol=symbol,
            window_days=window_days,
        )

    def _ranked_item(
        self,
        *,
        thesis: InvestmentThesis,
        similarity: HistoricalSimilarityReport | None,
        calibration: Mapping[str, Any],
        symbol_history: Mapping[str, Any],
        sector_history: Mapping[str, Any],
        sector: str,
        market_health: Mapping[str, Any],
        generated_at: datetime,
    ) -> RankedOpportunity:
        calibrated_confidence, confidence_samples, calibration_detail = (
            self._calibrated_confidence(
                raw_confidence=thesis.confidence,
                calibration=calibration,
            )
        )
        expected_return, return_detail = self._expected_return(
            similarity=similarity,
            symbol_history=symbol_history,
            sector_history=sector_history,
        )

        components = (
            self._component(
                code="THESIS_QUALITY",
                label="Thesis quality",
                ratio=thesis.score / 100.0,
                status="AVAILABLE",
                detail=(
                    f"Current investment thesis score is "
                    f"{thesis.score:.1f}/100."
                ),
            ),
            self._component(
                code="CALIBRATED_CONFIDENCE",
                label="Calibrated confidence",
                ratio=calibrated_confidence,
                status=(
                    "AVAILABLE" if confidence_samples >= 5 else "LIMITED"
                ),
                detail=calibration_detail,
            ),
            self._component(
                code="EVIDENCE_COVERAGE",
                label="Evidence coverage",
                ratio=thesis.confidence_coverage,
                status=(
                    "AVAILABLE"
                    if thesis.confidence_coverage >= 0.75
                    else "LIMITED"
                    if thesis.confidence_coverage > 0
                    else "UNAVAILABLE"
                ),
                detail=(
                    f"{thesis.confidence_coverage * 100:.1f}% of the "
                    "configured thesis capability weight is available."
                ),
            ),
            self._technical_macro_component(thesis.capabilities),
            self._historical_similarity_component(similarity),
            self._component(
                code="EXPECTED_RETURN",
                label="Expected return",
                ratio=(
                    None
                    if expected_return is None
                    else self._clamp(expected_return / 5.0)
                ),
                status=(
                    "AVAILABLE" if expected_return is not None else "UNAVAILABLE"
                ),
                detail=return_detail,
            ),
            self._symbol_sector_component(
                symbol_history=symbol_history,
                sector_history=sector_history,
                sector=sector,
            ),
            self._risk_component(thesis.risk_tier),
            self._component(
                code="EXECUTION_READINESS",
                label="Execution readiness",
                ratio=1.0 if thesis.eligible_for_execution else 0.0,
                status=(
                    "AVAILABLE" if thesis.eligible_for_execution else "BLOCKED"
                ),
                detail=(
                    "All recorded execution gates currently pass."
                    if thesis.eligible_for_execution
                    else (
                        f"Execution remains blocked by "
                        f"{len(thesis.blockers)} recorded gate(s)."
                    )
                ),
            ),
            self._market_data_component(market_health),
        )

        opportunity_score = round(
            self._clamp(
                sum(component.value for component in components) / 100.0
            )
            * 100.0,
            2,
        )
        measured_cases = (
            similarity.measured_case_count if similarity is not None else 0
        )
        matched_cases = (
            similarity.matched_case_count if similarity is not None else 0
        )
        data_quality = self._data_quality(
            coverage=thesis.confidence_coverage,
            measured_cases=measured_cases,
            confidence_samples=confidence_samples,
            market_status=str(market_health.get("status", "UNKNOWN")),
        )
        category = self._category(
            score=opportunity_score,
            eligible=thesis.eligible_for_execution,
            data_quality=data_quality,
        )
        positive = self._positive_contributors(components)
        penalties = self._penalties(
            components=components,
            blockers=thesis.blockers,
            warnings=thesis.warnings,
        )
        improvement_actions = self._improvement_actions(
            components=components,
            blockers=thesis.blockers,
        )

        return RankedOpportunity(
            rank=0,
            symbol=thesis.symbol,
            opportunity_score=opportunity_score,
            category=category,
            recommendation=thesis.recommendation,
            thesis_score=round(thesis.score, 2),
            raw_confidence=round(thesis.confidence, 6),
            calibrated_confidence=round(calibrated_confidence, 6),
            confidence_sample_count=confidence_samples,
            expected_return_percent=(
                None if expected_return is None else round(expected_return, 3)
            ),
            evidence_coverage_percent=round(
                thesis.confidence_coverage * 100.0,
                1,
            ),
            data_quality=data_quality,
            risk_tier=thesis.risk_tier,
            eligible_for_execution=thesis.eligible_for_execution,
            historical_match_count=matched_cases,
            measured_case_count=measured_cases,
            sector=sector,
            headline=thesis.headline,
            generated_at=generated_at,
            components=components,
            positive_contributors=positive,
            penalties=penalties,
            improvement_actions=improvement_actions,
            blockers=tuple(thesis.blockers),
            warnings=tuple(
                dict.fromkeys(
                    (
                        *thesis.warnings,
                        *(
                            similarity.warnings
                            if similarity is not None
                            else ()
                        ),
                    )
                )
            ),
        )

    def _component(
        self,
        *,
        code: str,
        label: str,
        ratio: float | None,
        status: str,
        detail: str,
    ) -> OpportunityRankingComponent:
        maximum = self.WEIGHTS[code]
        value = 0.0 if ratio is None else self._clamp(ratio) * maximum
        return OpportunityRankingComponent(
            code=code,
            label=label,
            value=round(value, 3),
            maximum=maximum,
            status=status,
            detail=detail,
        )

    def _technical_macro_component(
        self,
        capabilities: tuple[ThesisCapabilityAssessment, ...],
    ) -> OpportunityRankingComponent:
        index = {item.capability.upper(): item for item in capabilities}
        technical = index.get("TECHNICAL")
        macro = index.get("MACRO")

        technical_ratio = self._capability_ratio(technical)
        macro_ratio = self._capability_ratio(macro)
        ratio = (
            technical_ratio * 0.60
            + macro_ratio * 0.40
        )
        available_count = sum(
            item is not None and item.status == "AVAILABLE"
            for item in (technical, macro)
        )
        status = (
            "AVAILABLE" if available_count == 2 else
            "LIMITED" if available_count == 1 else
            "UNAVAILABLE"
        )
        detail = (
            f"Technical alignment contributes "
            f"{technical_ratio * 100:.1f}% and macro alignment contributes "
            f"{macro_ratio * 100:.1f}% of their available ranges."
        )
        return self._component(
            code="TECHNICAL_MACRO",
            label="Technical and macro alignment",
            ratio=ratio,
            status=status,
            detail=detail,
        )

    def _historical_similarity_component(
        self,
        similarity: HistoricalSimilarityReport | None,
    ) -> OpportunityRankingComponent:
        if similarity is None or similarity.matched_case_count == 0:
            return self._component(
                code="HISTORICAL_SIMILARITY",
                label="Historical similarity",
                ratio=None,
                status="UNAVAILABLE",
                detail="No qualifying historical analogue is available yet.",
            )

        similarity_ratio = self._clamp(
            (similarity.average_similarity_percent or 0.0) / 100.0
        )
        sample_maturity = self._clamp(
            similarity.measured_case_count / 10.0
        )
        win_ratio = self._clamp(
            (similarity.win_rate_percent or 0.0) / 100.0
        )
        ratio = (
            similarity_ratio * 0.50
            + win_ratio * sample_maturity * 0.35
            + sample_maturity * 0.15
        )
        status = (
            "AVAILABLE" if similarity.measured_case_count >= 5 else "LIMITED"
        )
        return self._component(
            code="HISTORICAL_SIMILARITY",
            label="Historical similarity",
            ratio=ratio,
            status=status,
            detail=(
                f"{similarity.matched_case_count} analogue(s) matched; "
                f"{similarity.measured_case_count} have measured outcomes, "
                f"with {similarity.win_rate_percent or 0.0:.1f}% directional "
                "success."
            ),
        )

    def _symbol_sector_component(
        self,
        *,
        symbol_history: Mapping[str, Any],
        sector_history: Mapping[str, Any],
        sector: str,
    ) -> OpportunityRankingComponent:
        symbol_count = int(symbol_history.get("measured_count", 0) or 0)
        sector_count = int(sector_history.get("measured_count", 0) or 0)
        if symbol_count == 0 and sector_count == 0:
            return self._component(
                code="SYMBOL_SECTOR_HISTORY",
                label="Symbol and sector history",
                ratio=None,
                status="UNAVAILABLE",
                detail=(
                    f"No measured symbol or {sector} sector outcomes are "
                    "available in the review window."
                ),
            )

        symbol_accuracy = self._clamp(
            float(symbol_history.get("directional_accuracy_percent", 0.0))
            / 100.0
        )
        sector_accuracy = self._clamp(
            float(sector_history.get("directional_accuracy_percent", 0.0))
            / 100.0
        )
        symbol_maturity = self._clamp(symbol_count / 10.0)
        sector_maturity = self._clamp(sector_count / 20.0)
        ratio = (
            symbol_accuracy * symbol_maturity * 0.65
            + sector_accuracy * sector_maturity * 0.35
        )
        return self._component(
            code="SYMBOL_SECTOR_HISTORY",
            label="Symbol and sector history",
            ratio=ratio,
            status=(
                "AVAILABLE" if symbol_count >= 5 or sector_count >= 10
                else "LIMITED"
            ),
            detail=(
                f"{symbol_count} measured {symbol_history.get('symbol', 'symbol')} "
                f"case(s) and {sector_count} measured {sector} sector case(s) "
                "contribute to the ranking."
            ),
        )

    def _risk_component(self, risk_tier: str) -> OpportunityRankingComponent:
        ratio = {
            "LOW": 1.0,
            "MEDIUM": 0.625,
            "HIGH": 0.25,
        }.get(risk_tier.upper(), 0.0)
        return self._component(
            code="RISK",
            label="Risk profile",
            ratio=ratio,
            status="AVAILABLE" if ratio else "UNAVAILABLE",
            detail=f"Current thesis risk tier is {risk_tier}.",
        )

    def _market_data_component(
        self,
        market_health: Mapping[str, Any],
    ) -> OpportunityRankingComponent:
        status = str(market_health.get("status", "UNKNOWN")).upper()
        circuit = str(market_health.get("circuit_state", "UNKNOWN")).upper()
        ratio = {
            "HEALTHY": 1.0,
            "DEGRADED": 0.5,
            "UNAVAILABLE": 0.0,
        }.get(status, 0.25)
        if circuit == "OPEN":
            ratio = min(ratio, 0.25)
        return self._component(
            code="DATA_FRESHNESS",
            label="Market-data health",
            ratio=ratio,
            status=status,
            detail=(
                f"Market-data resilience is {status}; circuit state is "
                f"{circuit}."
            ),
        )

    def _calibrated_confidence(
        self,
        *,
        raw_confidence: float,
        calibration: Mapping[str, Any],
    ) -> tuple[float, int, str]:
        raw_percent = raw_confidence * 100.0
        buckets = calibration.get("calibration_buckets", [])
        if not isinstance(buckets, list):
            buckets = []

        selected: Mapping[str, Any] | None = None
        for item in buckets:
            if not isinstance(item, Mapping):
                continue
            label = str(item.get("label", ""))
            if self._bucket_contains(label=label, value=raw_percent):
                selected = item
                break

        if selected is None:
            return (
                self._clamp(raw_confidence),
                0,
                "No matching measured confidence band is available; raw "
                "confidence is retained without fabrication.",
            )

        measured = int(selected.get("measured_count", 0) or 0)
        if measured <= 0:
            return (
                self._clamp(raw_confidence),
                0,
                f"The {selected.get('label', 'matching')} confidence band has "
                "no measured outcomes; raw confidence is retained.",
            )

        actual = self._clamp(
            float(selected.get("actual_accuracy_percent", 0.0)) / 100.0
        )
        blend_weight = min(measured / 20.0, 0.60)
        calibrated = (
            raw_confidence * (1.0 - blend_weight)
            + actual * blend_weight
        )
        return (
            self._clamp(calibrated),
            measured,
            f"Raw confidence of {raw_percent:.1f}% is conservatively blended "
            f"with {actual * 100:.1f}% measured accuracy across {measured} "
            "outcome(s) in the matching confidence band.",
        )

    def _expected_return(
        self,
        *,
        similarity: HistoricalSimilarityReport | None,
        symbol_history: Mapping[str, Any],
        sector_history: Mapping[str, Any],
    ) -> tuple[float | None, str]:
        values: list[tuple[float, float, str]] = []
        if (
            similarity is not None
            and similarity.average_directional_return_percent is not None
            and similarity.measured_case_count > 0
        ):
            values.append(
                (
                    float(similarity.average_directional_return_percent),
                    min(similarity.measured_case_count, 10),
                    "historical analogues",
                )
            )

        symbol_count = int(symbol_history.get("measured_count", 0) or 0)
        if symbol_count > 0:
            values.append(
                (
                    float(symbol_history.get("average_return_percent", 0.0)),
                    min(symbol_count, 10) * 0.75,
                    "symbol history",
                )
            )

        sector_count = int(sector_history.get("measured_count", 0) or 0)
        if sector_count > 0:
            values.append(
                (
                    float(sector_history.get("average_return_percent", 0.0)),
                    min(sector_count, 20) * 0.25,
                    "sector history",
                )
            )

        if not values:
            return (
                None,
                "No measured historical return sample is available; KAIRO "
                "does not fabricate an expected return.",
            )

        total_weight = sum(weight for _, weight, _ in values)
        expected = sum(value * weight for value, weight, _ in values) / total_weight
        sources = ", ".join(source for _, _, source in values)
        return (
            expected,
            f"Sample-weighted expected directional return is {expected:.3f}% "
            f"using {sources}.",
        )

    @staticmethod
    def _capability_ratio(
        capability: ThesisCapabilityAssessment | None,
    ) -> float:
        if (
            capability is None
            or capability.status != "AVAILABLE"
            or capability.score is None
            or capability.maximum <= 0
        ):
            return 0.0
        return OpportunityRankingService._clamp(
            float(capability.score) / float(capability.maximum)
        )

    @staticmethod
    def _bucket_contains(*, label: str, value: float) -> bool:
        if label == "Below 60%":
            return value < 60.0
        if label == "60–69%":
            return 60.0 <= value < 70.0
        if label == "70–79%":
            return 70.0 <= value < 80.0
        if label == "80–89%":
            return 80.0 <= value < 90.0
        if label == "90%+":
            return value >= 90.0
        return False

    @staticmethod
    def _data_quality(
        *,
        coverage: float,
        measured_cases: int,
        confidence_samples: int,
        market_status: str,
    ) -> str:
        status = market_status.upper()
        sample = measured_cases + confidence_samples
        if coverage >= 0.80 and sample >= 10 and status == "HEALTHY":
            return "STRONG"
        if coverage >= 0.60 and sample >= 3 and status != "UNAVAILABLE":
            return "MODERATE"
        if coverage >= 0.40 or sample > 0:
            return "LIMITED"
        return "INSUFFICIENT"

    @staticmethod
    def _category(*, score: float, eligible: bool, data_quality: str) -> str:
        if eligible and score >= 75.0:
            return "PRIORITY_READY"
        if not eligible and score >= 70.0:
            return "HIGH_POTENTIAL_BLOCKED"
        if data_quality in {"LIMITED", "INSUFFICIENT"} and score >= 45.0:
            return "PROMISING_IMMATURE"
        if score >= 60.0:
            return "WATCH"
        if data_quality == "INSUFFICIENT":
            return "INSUFFICIENT_DATA"
        return "MONITOR"

    @staticmethod
    def _positive_contributors(
        components: tuple[OpportunityRankingComponent, ...],
    ) -> tuple[str, ...]:
        ranked = sorted(
            (
                component
                for component in components
                if component.maximum > 0
                and component.value / component.maximum >= 0.55
            ),
            key=lambda item: item.value,
            reverse=True,
        )
        return tuple(
            f"{item.label}: {item.value:.1f}/{item.maximum:.1f}. "
            f"{item.detail}"
            for item in ranked[:4]
        )

    @staticmethod
    def _penalties(
        *,
        components: tuple[OpportunityRankingComponent, ...],
        blockers: tuple[str, ...],
        warnings: tuple[str, ...],
    ) -> tuple[str, ...]:
        component_penalties = [
            f"{item.label}: {item.detail}"
            for item in components
            if item.maximum > 0
            and item.value / item.maximum < 0.35
        ]
        return tuple(
            dict.fromkeys(
                (
                    *(f"Execution blocker: {item}" for item in blockers),
                    *component_penalties,
                    *(f"Warning: {item}" for item in warnings),
                )
            )
        )[:8]

    @staticmethod
    def _improvement_actions(
        *,
        components: tuple[OpportunityRankingComponent, ...],
        blockers: tuple[str, ...],
    ) -> tuple[str, ...]:
        actions = [f"Resolve execution gate: {item}" for item in blockers]
        actions.extend(
            f"Improve {item.label.lower()}: {item.detail}"
            for item in components
            if item.maximum > 0
            and item.value / item.maximum < 0.50
            and item.code != "EXECUTION_READINESS"
        )
        return tuple(dict.fromkeys(actions))[:6]

    def _utc_now(self) -> datetime:
        value = self._now_provider()
        if value.tzinfo is None:
            raise ValueError("Opportunity Ranking clock must be timezone-aware.")
        return value.astimezone(timezone.utc)

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(float(value), 1.0))
