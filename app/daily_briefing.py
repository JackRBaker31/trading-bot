from dataclasses import asdict, dataclass
from enum import Enum


class BriefingActionType(str, Enum):
    RUN_NEWS_RESEARCH = "RUN_NEWS_RESEARCH"
    RUN_STRATEGY_REPORT = "RUN_STRATEGY_REPORT"
    RUN_SHADOW_ANALYSIS = "RUN_SHADOW_ANALYSIS"
    REVIEW_UNRESOLVED_ORDERS = (
        "REVIEW_UNRESOLVED_ORDERS"
    )
    RUN_RECONCILIATION = "RUN_RECONCILIATION"
    REVIEW_TOP_OPPORTUNITY = (
        "REVIEW_TOP_OPPORTUNITY"
    )
    START_PAPER_TRADING = "START_PAPER_TRADING"
    WAIT_FOR_MORE_EVIDENCE = (
        "WAIT_FOR_MORE_EVIDENCE"
    )


class BriefingPriority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True)
class BriefingAction:
    action: BriefingActionType
    priority: BriefingPriority
    label: str
    reason: str
    endpoint: str | None = None
    method: str | None = None
    symbol: str | None = None

    def to_dictionary(self) -> dict[str, object]:
        payload = asdict(self)
        payload["action"] = self.action.value
        payload["priority"] = self.priority.value
        return payload


@dataclass(frozen=True)
class DailyBriefing:
    generated_at: str
    headline: str
    summary: str
    market_outlook: str
    confidence: float
    trading_readiness: str
    evidence_quality: str
    graduation_status: str
    graduation_checks_passed: int
    graduation_total_checks: int
    top_opportunity: dict[str, object] | None
    key_points: tuple[str, ...]
    warnings: tuple[str, ...]
    actions: tuple[BriefingAction, ...]
    is_stale: bool
    trading_impact: str = "NONE"

    def to_dictionary(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at,
            "headline": self.headline,
            "summary": self.summary,
            "market_outlook": self.market_outlook,
            "confidence": self.confidence,
            "trading_readiness": self.trading_readiness,
            "evidence_quality": self.evidence_quality,
            "graduation_status": self.graduation_status,
            "graduation_checks_passed": (
                self.graduation_checks_passed
            ),
            "graduation_total_checks": (
                self.graduation_total_checks
            ),
            "top_opportunity": self.top_opportunity,
            "key_points": list(self.key_points),
            "warnings": list(self.warnings),
            "actions": [
                action.to_dictionary()
                for action in self.actions
            ],
            "is_stale": self.is_stale,
            "trading_impact": self.trading_impact,
        }
