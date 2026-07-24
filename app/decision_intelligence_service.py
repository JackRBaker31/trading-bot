from collections.abc import Callable
from datetime import datetime, timezone
from uuid import uuid4

from app.copilot_overview_models import (
    CopilotOverview,
)
from app.decision_trace_models import (
    DecisionTrace,
    DecisionTraceStage,
)
from app.decision_trace_repository import (
    DecisionTraceRepository,
)


class DecisionIntelligenceService:
    def __init__(
        self,
        *,
        repository: (
            DecisionTraceRepository
        ),
        overview_provider: Callable[
            [],
            CopilotOverview,
        ],
        now_provider: Callable[
            [],
            datetime,
        ] | None = None,
    ) -> None:
        self._repository = repository
        self._overview_provider = (
            overview_provider
        )
        self._now_provider = (
            now_provider
            or (
                lambda: datetime.now(
                    timezone.utc
                )
            )
        )

    def initialize(self) -> None:
        self._repository.initialize()

    def capture(
        self,
    ) -> DecisionTrace:
        trace = self._build_trace(
            overview=(
                self._overview_provider()
            )
        )

        self._repository.save(
            trace=trace
        )

        return trace

    def latest(
        self,
        *,
        capture_current: bool = True,
    ) -> DecisionTrace:
        if capture_current:
            return self.capture()

        existing = (
            self._repository.latest()
        )

        if existing is not None:
            return existing

        return self.capture()

    def list_recent(
        self,
        *,
        limit: int = 50,
        capture_current: bool = True,
    ) -> tuple[
        DecisionTrace,
        ...
    ]:
        if capture_current:
            self.capture()

        return (
            self._repository
            .list_recent(
                limit=limit
            )
        )

    def _build_trace(
        self,
        *,
        overview: CopilotOverview,
    ) -> DecisionTrace:
        intelligence = (
            overview
            .trading_intelligence
        )
        graduation = (
            overview.graduation
        )
        blockers = (
            self._blockers(
                overview=overview
            )
        )

        trade_ready = (
            intelligence
            .trading_readiness
            == "READY"
            and graduation.ready
            and not blockers
        )

        confidence = float(
            intelligence.confidence
        )

        stages = (
            DecisionTraceStage(
                sequence=1,
                stage="RESEARCH",
                status=(
                    "PASS"
                    if (
                        intelligence
                        .evidence_quality
                        .upper()
                        not in {
                            "LOW",
                            "VERY_LOW",
                            "INSUFFICIENT",
                            "UNKNOWN",
                        }
                    )
                    else "BLOCKED"
                ),
                title=(
                    "Research Evidence"
                ),
                summary=(
                    "Research evidence "
                    f"quality is "
                    f"{intelligence.evidence_quality}."
                ),
                evidence=(
                    (
                        "Market outlook: "
                        f"{intelligence.market_outlook}"
                    ),
                    (
                        "Total signals: "
                        f"{intelligence.signal_count}"
                    ),
                ),
            ),
            DecisionTraceStage(
                sequence=2,
                stage="SIGNALS",
                status=(
                    "PASS"
                    if (
                        intelligence
                        .actionable_signal_count
                        > 0
                    )
                    else "BLOCKED"
                ),
                title=(
                    "Signal Qualification"
                ),
                summary=(
                    f"{intelligence.actionable_signal_count} "
                    "actionable signal(s) "
                    f"from "
                    f"{intelligence.signal_count} "
                    "current signal(s)."
                ),
                evidence=(
                    (
                        "Confidence: "
                        f"{confidence:.1f}"
                    ),
                ),
            ),
            DecisionTraceStage(
                sequence=3,
                stage="READINESS",
                status=(
                    "PASS"
                    if (
                        intelligence
                        .trading_readiness
                        == "READY"
                    )
                    else "BLOCKED"
                ),
                title=(
                    "Trading Readiness"
                ),
                summary=(
                    "Platform trading "
                    f"readiness is "
                    f"{intelligence.trading_readiness}."
                ),
                evidence=(
                    (
                        "Platform status: "
                        f"{overview.platform.overall_status}"
                    ),
                ),
            ),
            DecisionTraceStage(
                sequence=4,
                stage="GRADUATION",
                status=(
                    "PASS"
                    if graduation.ready
                    else "BLOCKED"
                ),
                title=(
                    "Graduation Gate"
                ),
                summary=(
                    f"{graduation.passed_checks} "
                    f"of "
                    f"{graduation.total_checks} "
                    "graduation check(s) "
                    "passed."
                ),
                evidence=tuple(
                    check.reason
                    or (
                        f"{check.name} "
                        "has not passed."
                    )
                    for check
                    in graduation.failed_checks
                ),
            ),
            DecisionTraceStage(
                sequence=5,
                stage="DECISION",
                status=(
                    "PASS"
                    if trade_ready
                    else "BLOCKED"
                ),
                title=(
                    "Final Decision"
                ),
                summary=(
                    "KAIRO is trade ready."
                    if trade_ready
                    else (
                        "KAIRO withheld "
                        "execution."
                    )
                ),
                evidence=(
                    blockers
                    if blockers
                    else (
                        "No deterministic "
                        "blockers were found.",
                    )
                ),
            ),
        )

        return DecisionTrace(
            trace_id=str(uuid4()),
            created_at=self._utc_now(),
            symbol=None,
            decision=(
                "TRADE_READY"
                if trade_ready
                else "NO_TRADE"
            ),
            confidence=confidence,
            trading_readiness=(
                intelligence
                .trading_readiness
            ),
            graduation_ready=(
                graduation.ready
            ),
            summary=(
                "Current evidence "
                "supports trade readiness."
                if trade_ready
                else (
                    "Execution was withheld "
                    f"because "
                    f"{len(blockers)} "
                    "deterministic blocker(s) "
                    "remain."
                )
            ),
            stages=stages,
            blockers=blockers,
        )

    @staticmethod
    def _blockers(
        *,
        overview: CopilotOverview,
    ) -> tuple[str, ...]:
        intelligence = (
            overview
            .trading_intelligence
        )
        graduation = (
            overview.graduation
        )
        blockers: list[str] = []

        if (
            intelligence
            .trading_readiness
            != "READY"
        ):
            blockers.append(
                "Trading readiness has "
                "not reached READY."
            )

        confidence = float(
            intelligence.confidence
        )
        confidence_percent = (
            confidence * 100
            if confidence <= 1
            else confidence
        )

        if confidence_percent < 80:
            blockers.append(
                "Intelligence confidence "
                "is below 80%."
            )

        if (
            intelligence
            .actionable_signal_count
            <= 0
        ):
            blockers.append(
                "No actionable signals "
                "are currently available."
            )

        if (
            intelligence
            .evidence_quality
            .upper()
            in {
                "LOW",
                "VERY_LOW",
                "INSUFFICIENT",
                "UNKNOWN",
            }
        ):
            blockers.append(
                "Evidence quality is not "
                "strong enough."
            )

        blockers.extend(
            check.reason
            or (
                f"{check.name} "
                "has not passed."
            )
            for check
            in graduation.failed_checks
        )

        return tuple(
            dict.fromkeys(
                blockers
            )
        )

    def _utc_now(
        self,
    ) -> datetime:
        value = self._now_provider()

        if value.tzinfo is None:
            raise ValueError(
                "Decision Intelligence "
                "clock must be "
                "timezone-aware."
            )

        return value.astimezone(
            timezone.utc
        )
