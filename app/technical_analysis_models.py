from dataclasses import asdict, dataclass
from datetime import date


@dataclass(frozen=True)
class TechnicalMetric:
    code: str
    label: str
    value: float | None
    display_value: str
    score: float
    maximum: float
    stance: str
    detail: str

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TechnicalAnalysis:
    symbol: str
    as_of_date: date
    bar_count: int
    score: float
    maximum: float
    confidence: float
    stance: str
    trend: str
    momentum: str
    volatility: str
    volume_confirmation: str
    price_structure: str
    latest_close: float
    metrics: tuple[
        TechnicalMetric,
        ...
    ]
    evidence: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "as_of_date": (
                self.as_of_date.isoformat()
            ),
            "bar_count": self.bar_count,
            "score": self.score,
            "maximum": self.maximum,
            "confidence": self.confidence,
            "stance": self.stance,
            "trend": self.trend,
            "momentum": self.momentum,
            "volatility": self.volatility,
            "volume_confirmation": (
                self.volume_confirmation
            ),
            "price_structure": (
                self.price_structure
            ),
            "latest_close": (
                self.latest_close
            ),
            "metrics": [
                metric.to_dictionary()
                for metric in self.metrics
            ],
            "evidence": list(self.evidence),
            "warnings": list(self.warnings),
        }
