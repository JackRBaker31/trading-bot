from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class NewsConfidenceFactor:
    code: str
    label: str
    contribution: float
    detail: str

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class NewsConfidenceResult:
    confidence: float
    factors: tuple[NewsConfidenceFactor, ...]
