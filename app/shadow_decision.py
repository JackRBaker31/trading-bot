from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum


class ShadowAction(str, Enum):
    MONITOR = "MONITOR"
    WATCH = "WATCH"
    CONSIDER_LONG = "CONSIDER_LONG"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ShadowDecision:
    decision_id: str
    article_id: str
    symbol: str
    created_at: datetime
    model_version: str
    action: ShadowAction
    score: float
    confidence: float
    sentiment: str
    event_type: str
    is_material: bool
    headline: str
    eligible_for_trade: bool
    reasons: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    reference_price: float | None = None
    reference_captured_at: datetime | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("decision_id", self.decision_id),
            ("article_id", self.article_id),
            ("symbol", self.symbol),
            ("model_version", self.model_version),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required.")

        if self.created_at.tzinfo is None:
            raise ValueError(
                "Shadow decision time must be timezone-aware."
            )

        if not 0 <= self.score <= 100:
            raise ValueError(
                "Shadow decision score must be between 0 and 100."
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "Shadow decision confidence must be between 0 and 1."
            )

        if self.reference_price is not None and self.reference_price <= 0:
            raise ValueError(
                "Shadow reference price must be positive."
            )

        if (
            self.reference_captured_at is not None
            and self.reference_captured_at.tzinfo is None
        ):
            raise ValueError(
                "Shadow reference time must be timezone-aware."
            )

        object.__setattr__(self, "symbol", self.symbol.upper().strip())
        object.__setattr__(self, "action", ShadowAction(self.action))

    def to_dictionary(self) -> dict[str, object]:
        payload = asdict(self)
        payload["action"] = self.action.value
        payload["created_at"] = self.created_at.isoformat()
        payload["reference_captured_at"] = (
            None
            if self.reference_captured_at is None
            else self.reference_captured_at.isoformat()
        )
        payload["reasons"] = list(self.reasons)
        payload["blocking_reasons"] = list(self.blocking_reasons)
        return payload
