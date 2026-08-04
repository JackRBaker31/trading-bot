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
        return {
            "eligible": self.eligible,
            "checks_passed": self.checks_passed,
            "total_checks": self.total_checks,
            "checks_remaining": max(
                0,
                self.total_checks - self.checks_passed,
            ),
            "checks": [
                {
                    **check.to_dictionary(),
                    "description": check.reason,
                }
                for check in self.checks
            ],
            "failed_checks": list(self.failed_checks),
            "status": self.status,
            "stage": self.status,
            "trading_impact": self.trading_impact,
        }
