from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Protocol

from app.intelligence_snapshot import (
    EvidenceQuality,
    IntelligenceFreshness,
    IntelligenceOpportunity,
    IntelligenceSnapshot,
    MarketOutlook,
    OpportunityClassification,
    TradingReadiness,
)
from app.operations_query_service import (
    OperationsQueryRequest,
)
from app.system_status_service import SystemStatusRequest


class SystemStatusServiceLike(Protocol):
    def get_status(self, *, request: SystemStatusRequest):
        ...


class ResearchQueryServiceLike(Protocol):
    def get_latest_report(self):
        ...

    def list_signals(self, **kwargs):
        ...

    def get_news_summary(self):
        ...


class OperationsQueryServiceLike(Protocol):
    def get_risk_status(self, *, request: OperationsQueryRequest):
        ...

    def get_latest_reconciliation(
        self,
        *,
        request: OperationsQueryRequest,
    ):
        ...


class PaperTradingControllerLike(Protocol):
    def get_status(self):
        ...


class IntelligenceService:
    def __init__(
        self,
        *,
        system_status_service: SystemStatusServiceLike,
        research_query_service: ResearchQueryServiceLike,
        operations_query_service: OperationsQueryServiceLike,
        paper_trading_controller: PaperTradingControllerLike,
        now_provider: Callable[[], datetime] | None = None,
        research_stale_after: timedelta = timedelta(hours=24),
        signal_stale_after: timedelta = timedelta(hours=6),
        high_confidence_threshold: float = 0.80,
        opportunity_limit: int = 3,
    ) -> None:
        self._system_status_service = system_status_service
        self._research_query_service = research_query_service
        self._operations_query_service = operations_query_service
        self._paper_trading_controller = paper_trading_controller
        self._now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )
        self._research_stale_after = research_stale_after
        self._signal_stale_after = signal_stale_after
        self._high_confidence_threshold = high_confidence_threshold
        self._opportunity_limit = opportunity_limit

    def get_snapshot(self) -> IntelligenceSnapshot:
        now = self._utc_now()
        system = self._system_status_service.get_status(
            request=SystemStatusRequest()
        )
        report = self._research_query_service.get_latest_report()
        summary = self._research_query_service.get_news_summary()
        signals_page = self._research_query_service.list_signals(
            offset=0,
            limit=500,
        )
        risk = self._operations_query_service.get_risk_status(
            request=OperationsQueryRequest()
        )
        reconciliation = (
            self._operations_query_service
            .get_latest_reconciliation(
                request=OperationsQueryRequest()
            )
        )
        paper_status = (
            self._paper_trading_controller.get_status()
        )

        signals = tuple(signals_page.items)
        active_signals = tuple(
            signal
            for signal in signals
            if not self._is_expired(
                str(signal["expires_at"]),
                now,
            )
        )
        high_confidence = tuple(
            signal
            for signal in active_signals
            if float(signal["confidence"])
            >= self._high_confidence_threshold
        )
        material = tuple(
            signal
            for signal in active_signals
            if bool(signal["is_material"])
        )
        actionable = tuple(
            signal
            for signal in high_confidence
            if bool(signal["is_material"])
            and float(signal["sentiment"]) > 0
        )

        evidence_sample_count = int(
            summary.get("outcome_count", 0)
        )
        evidence_quality = self._evidence_quality(
            evidence_sample_count
        )
        freshness = self._build_freshness(
            now=now,
            report=report,
            signals=signals,
        )
        readiness_reasons = self._readiness_reasons(
            application_mode=system.application_mode,
            paper_enabled=risk.paper_trading_enabled,
            broker_environment=risk.broker_environment,
            execution_permission=(
                risk.execution_permission_confirmed
            ),
            reconciliation_available=(
                reconciliation.available
            ),
            reconciliation_safe=(
                reconciliation.safe_to_start
            ),
            unresolved_orders=(
                reconciliation.unresolved_order_count
            ),
        )
        readiness = (
            TradingReadiness.READY
            if not readiness_reasons
            else TradingReadiness.NOT_READY
        )
        risk_warnings = self._risk_warnings(
            freshness=freshness,
            evidence_quality=evidence_quality,
            unresolved_orders=(
                reconciliation.unresolved_order_count
            ),
            report=report,
        )
        opportunities = self._rank_opportunities(
            signals=active_signals,
            approved_symbols=set(
                risk.approved_symbols
            ),
            readiness=readiness,
            evidence_quality=evidence_quality,
        )
        outlook = self._market_outlook(
            report=report,
            freshness=freshness,
            positive_actionable_count=len(actionable),
            signal_count=len(active_signals),
        )
        confidence = self._confidence(
            report=report,
            evidence_quality=evidence_quality,
            freshness=freshness,
            actionable_count=len(actionable),
        )
        actions = self._recommended_actions(
            readiness_reasons=readiness_reasons,
            freshness=freshness,
            evidence_quality=evidence_quality,
            opportunities=opportunities,
        )

        return IntelligenceSnapshot(
            generated_at=now.isoformat(),
            market_outlook=outlook,
            confidence=confidence,
            trading_readiness=readiness,
            readiness_reasons=readiness_reasons,
            research_verdict=(
                None
                if report is None
                else str(report.get("verdict"))
            ),
            evidence_quality=evidence_quality,
            evidence_sample_count=evidence_sample_count,
            signal_count=len(active_signals),
            high_confidence_signal_count=len(
                high_confidence
            ),
            material_event_count=len(material),
            actionable_signal_count=len(actionable),
            paper_trading_state=(
                paper_status.state.value
            ),
            top_opportunities=opportunities,
            risk_warnings=risk_warnings,
            recommended_actions=actions,
            freshness=freshness,
        )

    def _rank_opportunities(
        self,
        *,
        signals: tuple[dict[str, object], ...],
        approved_symbols: set[str],
        readiness: TradingReadiness,
        evidence_quality: EvidenceQuality,
    ) -> tuple[IntelligenceOpportunity, ...]:
        best_by_symbol: dict[str, dict[str, object]] = {}

        for signal in signals:
            symbol = str(signal["symbol"]).upper()
            score_breakdown = {
                "confidence": round(
                    float(signal["confidence"]) * 45,
                    2,
                ),
                "relevance": round(
                    float(signal["relevance"]) * 25,
                    2,
                ),
                "sentiment": round(
                    max(0.0, float(signal["sentiment"]))
                    * 15,
                    2,
                ),
                "materiality": (
                    15.0
                    if bool(signal["is_material"])
                    else 0.0
                ),
            }
            score = round(
                sum(score_breakdown.values()),
                2,
            )
            candidate = {
                "signal": signal,
                "score": score,
                "breakdown": score_breakdown,
            }
            existing = best_by_symbol.get(symbol)
            if (
                existing is None
                or score > float(existing["score"])
            ):
                best_by_symbol[symbol] = candidate

        ordered = sorted(
            best_by_symbol.items(),
            key=lambda item: float(item[1]["score"]),
            reverse=True,
        )[: self._opportunity_limit]

        results: list[IntelligenceOpportunity] = []
        for rank, (symbol, candidate) in enumerate(
            ordered,
            start=1,
        ):
            signal = candidate["signal"]
            assert isinstance(signal, dict)
            score = float(candidate["score"])
            blocking: list[str] = []

            if symbol not in approved_symbols:
                blocking.append(
                    "Symbol is not approved by the risk policy."
                )
            if readiness is TradingReadiness.NOT_READY:
                blocking.append(
                    "Platform trading-readiness checks have not passed."
                )
            if evidence_quality in {
                EvidenceQuality.VERY_LOW,
                EvidenceQuality.LOW,
            }:
                blocking.append(
                    "Historical news-outcome evidence is still limited."
                )

            eligible = not blocking
            if blocking:
                classification = (
                    OpportunityClassification.BLOCKED
                )
            elif score >= 80:
                classification = (
                    OpportunityClassification.CANDIDATE
                )
            elif score >= 65:
                classification = (
                    OpportunityClassification.WATCH
                )
            else:
                classification = (
                    OpportunityClassification.MONITOR
                )

            reasons = [
                "Signal confidence contributes "
                f"{candidate['breakdown']['confidence']:.1f} points.",
                "News relevance contributes "
                f"{candidate['breakdown']['relevance']:.1f} points.",
            ]
            if bool(signal["is_material"]):
                reasons.append(
                    "The source event was classified as material."
                )
            if float(signal["sentiment"]) > 0:
                reasons.append(
                    "The signal has positive sentiment."
                )

            results.append(
                IntelligenceOpportunity(
                    article_id=str(signal["article_id"]),
                    rank=rank,
                    symbol=symbol,
                    score=score,
                    classification=classification,
                    confidence=float(signal["confidence"]),
                    sentiment=str(signal["sentiment_name"]),
                    is_material=bool(signal["is_material"]),
                    event_type=str(signal["event_type"]),
                    headline=str(signal["headline"]),
                    published_at=str(signal["published_at"]),
                    eligible_for_trade=eligible,
                    reasons=tuple(reasons),
                    blocking_reasons=tuple(blocking),
                    score_breakdown=dict(
                        candidate["breakdown"]
                    ),
                )
            )

        return tuple(results)

    def _build_freshness(
        self,
        *,
        now: datetime,
        report: dict[str, object] | None,
        signals: tuple[dict[str, object], ...],
    ) -> IntelligenceFreshness:
        reasons: list[str] = []
        latest_research_at = (
            None
            if report is None
            else self._optional_string(
                report.get("generated_at")
            )
        )
        latest_signal_at = (
            None
            if not signals
            else max(
                str(signal["published_at"])
                for signal in signals
            )
        )

        if latest_research_at is None:
            reasons.append(
                "No strategy research report is available."
            )
        elif now - self._parse_datetime(
            latest_research_at
        ) > self._research_stale_after:
            reasons.append(
                "The latest strategy report is stale."
            )

        if latest_signal_at is None:
            reasons.append(
                "No news signals are available."
            )
        elif now - self._parse_datetime(
            latest_signal_at
        ) > self._signal_stale_after:
            reasons.append(
                "The latest news signal is stale."
            )

        return IntelligenceFreshness(
            is_stale=bool(reasons),
            latest_research_at=latest_research_at,
            latest_signal_at=latest_signal_at,
            stale_reasons=tuple(reasons),
        )

    @staticmethod
    def _readiness_reasons(
        *,
        application_mode: str,
        paper_enabled: bool,
        broker_environment: str,
        execution_permission: bool,
        reconciliation_available: bool,
        reconciliation_safe: bool,
        unresolved_orders: int,
    ) -> tuple[str, ...]:
        reasons: list[str] = []
        if application_mode.upper() != "PAPER":
            reasons.append(
                "Application mode is not PAPER."
            )
        if not paper_enabled:
            reasons.append(
                "Paper trading is disabled."
            )
        if broker_environment.upper() != "DEMO":
            reasons.append(
                "Broker environment is not DEMO."
            )
        if not execution_permission:
            reasons.append(
                "DEMO order execution permission is not confirmed."
            )
        if not reconciliation_available:
            reasons.append(
                "No successful reconciliation is available."
            )
        elif not reconciliation_safe:
            reasons.append(
                "Reconciliation has not marked the platform safe to start."
            )
        if unresolved_orders > 0:
            reasons.append(
                f"{unresolved_orders} unresolved order(s) require attention."
            )
        return tuple(reasons)

    @staticmethod
    def _risk_warnings(
        *,
        freshness: IntelligenceFreshness,
        evidence_quality: EvidenceQuality,
        unresolved_orders: int,
        report: dict[str, object] | None,
    ) -> tuple[str, ...]:
        warnings: list[str] = list(
            freshness.stale_reasons
        )
        if evidence_quality in {
            EvidenceQuality.VERY_LOW,
            EvidenceQuality.LOW,
        }:
            warnings.append(
                "AI news evidence is not yet statistically mature."
            )
        if unresolved_orders:
            warnings.append(
                "Unresolved orders prevent reliable automated operation."
            )
        if report is not None and str(
            report.get("verdict", "")
        ).upper() == "REJECTED":
            warnings.append(
                "The latest strategy research verdict is REJECTED."
            )
        return tuple(dict.fromkeys(warnings))

    @staticmethod
    def _market_outlook(
        *,
        report: dict[str, object] | None,
        freshness: IntelligenceFreshness,
        positive_actionable_count: int,
        signal_count: int,
    ) -> MarketOutlook:
        if report is None:
            return MarketOutlook.INSUFFICIENT_DATA
        verdict = str(report.get("verdict", "")).upper()
        if verdict == "REJECTED":
            return MarketOutlook.UNFAVOURABLE
        if freshness.is_stale or signal_count == 0:
            return MarketOutlook.CAUTIOUS
        if verdict == "PROMISING" and positive_actionable_count > 0:
            return MarketOutlook.PROMISING
        return MarketOutlook.CAUTIOUS

    @staticmethod
    def _confidence(
        *,
        report: dict[str, object] | None,
        evidence_quality: EvidenceQuality,
        freshness: IntelligenceFreshness,
        actionable_count: int,
    ) -> float:
        if report is None:
            return 0.0

        passed = float(
            report.get("passed_check_count", 0)
        )
        total = max(
            1.0,
            float(report.get("total_check_count", 1)),
        )
        report_score = passed / total
        evidence_scores = {
            EvidenceQuality.VERY_LOW: 0.20,
            EvidenceQuality.LOW: 0.40,
            EvidenceQuality.MODERATE: 0.70,
            EvidenceQuality.STRONG: 1.00,
        }
        freshness_score = (
            0.30 if freshness.is_stale else 1.00
        )
        opportunity_score = min(
            1.0,
            actionable_count / 3,
        )
        confidence = (
            report_score * 0.50
            + evidence_scores[evidence_quality] * 0.25
            + freshness_score * 0.15
            + opportunity_score * 0.10
        )
        caps = {
            EvidenceQuality.VERY_LOW: 0.55,
            EvidenceQuality.LOW: 0.70,
            EvidenceQuality.MODERATE: 0.85,
            EvidenceQuality.STRONG: 0.95,
        }
        return round(
            min(confidence, caps[evidence_quality]),
            3,
        )

    @staticmethod
    def _recommended_actions(
        *,
        readiness_reasons: tuple[str, ...],
        freshness: IntelligenceFreshness,
        evidence_quality: EvidenceQuality,
        opportunities: tuple[IntelligenceOpportunity, ...],
    ) -> tuple[str, ...]:
        actions: list[str] = []
        for reason in readiness_reasons:
            if "reconciliation" in reason.lower():
                actions.append(
                    "Run and review broker reconciliation."
                )
            elif "execution permission" in reason.lower():
                actions.append(
                    "Confirm DEMO execution permission only when ready."
                )
            elif "unresolved order" in reason.lower():
                actions.append(
                    "Investigate unresolved orders before starting trading."
                )
        if freshness.is_stale:
            actions.append(
                "Refresh strategy and news research."
            )
        if evidence_quality in {
            EvidenceQuality.VERY_LOW,
            EvidenceQuality.LOW,
        }:
            actions.append(
                "Continue collecting shadow outcomes before using AI signals for decisions."
            )
        if opportunities:
            actions.append(
                f"Review {opportunities[0].symbol}, the highest-ranked current opportunity."
            )
        if not actions:
            actions.append(
                "Review current opportunities and risk limits before starting DEMO paper trading."
            )
        return tuple(dict.fromkeys(actions))

    @staticmethod
    def _evidence_quality(
        outcome_count: int,
    ) -> EvidenceQuality:
        if outcome_count < 10:
            return EvidenceQuality.VERY_LOW
        if outcome_count < 50:
            return EvidenceQuality.LOW
        if outcome_count < 150:
            return EvidenceQuality.MODERATE
        return EvidenceQuality.STRONG

    @staticmethod
    def _is_expired(
        value: str,
        now: datetime,
    ) -> bool:
        return IntelligenceService._parse_datetime(
            value
        ) <= now

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _optional_string(
        value: object,
    ) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    def _utc_now(self) -> datetime:
        value = self._now_provider()
        if value.tzinfo is None:
            raise ValueError(
                "Intelligence clock must be timezone-aware."
            )
        return value.astimezone(timezone.utc)
