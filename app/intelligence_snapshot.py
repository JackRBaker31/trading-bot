from dataclasses import asdict, dataclass
from enum import Enum


class MarketOutlook(str, Enum):
    PROMISING = "PROMISING"
    CAUTIOUS = "CAUTIOUS"
    UNFAVOURABLE = "UNFAVOURABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class TradingReadiness(str, Enum):
    READY = "READY"
    NOT_READY = "NOT_READY"


class EvidenceQuality(str, Enum):
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class OpportunityClassification(str, Enum):
    MONITOR = "MONITOR"
    WATCH = "WATCH"
    CANDIDATE = "CANDIDATE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class IntelligenceOpportunity:
    article_id: str
    rank: int
    symbol: str
    score: float
    classification: OpportunityClassification
    confidence: float
    sentiment: str
    is_material: bool
    event_type: str
    headline: str
    published_at: str
    eligible_for_trade: bool
    reasons: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    score_breakdown: dict[str, float]

    def to_dictionary(self) -> dict[str, object]:
        payload = asdict(self)
        payload["classification"] = self.classification.value
        return payload


@dataclass(frozen=True)
class IntelligenceFreshness:
    is_stale: bool
    latest_research_at: str | None
    latest_signal_at: str | None
    stale_reasons: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class IntelligenceSnapshot:
    generated_at: str
    market_outlook: MarketOutlook
    confidence: float
    trading_readiness: TradingReadiness
    readiness_reasons: tuple[str, ...]
    research_verdict: str | None
    evidence_quality: EvidenceQuality
    evidence_sample_count: int
    signal_count: int
    high_confidence_signal_count: int
    material_event_count: int
    actionable_signal_count: int
    paper_trading_state: str
    top_opportunities: tuple[IntelligenceOpportunity, ...]
    risk_warnings: tuple[str, ...]
    recommended_actions: tuple[str, ...]
    freshness: IntelligenceFreshness

    def to_dictionary(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at,
            "market_outlook": self.market_outlook.value,
            "confidence": self.confidence,
            "trading_readiness": self.trading_readiness.value,
            "readiness_reasons": list(self.readiness_reasons),
            "research_verdict": self.research_verdict,
            "evidence_quality": self.evidence_quality.value,
            "evidence_sample_count": self.evidence_sample_count,
            "signal_count": self.signal_count,
            "high_confidence_signal_count": (
                self.high_confidence_signal_count
            ),
            "material_event_count": self.material_event_count,
            "actionable_signal_count": self.actionable_signal_count,
            "paper_trading_state": self.paper_trading_state,
            "top_opportunities": [
                opportunity.to_dictionary()
                for opportunity in self.top_opportunities
            ],
            "risk_warnings": list(self.risk_warnings),
            "recommended_actions": list(self.recommended_actions),
            "freshness": self.freshness.to_dictionary(),
        }
