from dataclasses import asdict, dataclass
from datetime import date


@dataclass(frozen=True)
class MacroMetric:
    code: str
    label: str
    value: float | None
    display_value: str
    score: float
    maximum: float
    stance: str
    detail: str

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MacroAnalysis:
    as_of_date: date
    score: float
    maximum: float
    confidence: float
    stance: str
    regime: str
    broad_market_trend: str
    growth_leadership: str
    rate_pressure: str
    volatility_regime: str
    metrics: tuple[MacroMetric, ...]
    evidence: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "as_of_date": self.as_of_date.isoformat(),
            "score": self.score,
            "maximum": self.maximum,
            "confidence": self.confidence,
            "stance": self.stance,
            "regime": self.regime,
            "broad_market_trend": self.broad_market_trend,
            "growth_leadership": self.growth_leadership,
            "rate_pressure": self.rate_pressure,
            "volatility_regime": self.volatility_regime,
            "metrics": [item.to_dictionary() for item in self.metrics],
            "evidence": list(self.evidence),
            "warnings": list(self.warnings),
        }
