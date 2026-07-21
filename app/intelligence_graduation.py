from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class GraduationCheck:
    name: str
    passed: bool
    actual: object
    required: object
    reason: str

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class IntelligenceGraduationStatus:
    eligible: bool
    checks_passed: int
    total_checks: int
    checks: tuple[GraduationCheck, ...]
    failed_checks: tuple[str, ...]
    status: str
    trading_impact: str = "NONE"

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)
