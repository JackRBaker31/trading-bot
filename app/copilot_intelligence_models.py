from dataclasses import (
    asdict,
    dataclass,
    field,
)


@dataclass(frozen=True)
class CopilotIntelligenceOverview:
    trading_readiness: str
    market_outlook: str
    confidence: float
    signal_count: int
    actionable_signal_count: int
    evidence_quality: str

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CopilotGraduationCheck:
    name: str
    passed: bool
    reason: str | None = None

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CopilotGraduationOverview:
    ready: bool
    passed_checks: int
    total_checks: int
    checks: tuple[
        CopilotGraduationCheck,
        ...
    ] = field(default_factory=tuple)

    @property
    def failed_checks(
        self,
    ) -> tuple[
        CopilotGraduationCheck,
        ...
    ]:
        return tuple(
            check
            for check in self.checks
            if not check.passed
        )

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "ready": self.ready,
            "passed_checks": (
                self.passed_checks
            ),
            "total_checks": (
                self.total_checks
            ),
            "failed_checks": len(
                self.failed_checks
            ),
            "checks": [
                check.to_dictionary()
                for check in self.checks
            ],
        }


@dataclass(frozen=True)
class CopilotTradingIntelligence:
    intelligence: (
        CopilotIntelligenceOverview
    )
    graduation: (
        CopilotGraduationOverview
    )
    blockers: tuple[str, ...] = (
        field(default_factory=tuple)
    )

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "intelligence": (
                self.intelligence
                .to_dictionary()
            ),
            "graduation": (
                self.graduation
                .to_dictionary()
            ),
            "blockers": list(
                self.blockers
            ),
        }