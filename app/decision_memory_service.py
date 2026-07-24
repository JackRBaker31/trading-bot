import hashlib
import json
from collections.abc import Callable
from datetime import datetime, timezone
from uuid import uuid4

from app.decision_memory_models import (
    DecisionMemoryCapability,
    DecisionMemoryCaptureResult,
    DecisionMemoryOverview,
    DecisionMemoryRecord,
)
from app.decision_memory_repository import (
    DecisionMemoryRepository,
)
from app.investment_thesis_models import (
    InvestmentThesis,
    InvestmentThesisReport,
)


NowProvider = Callable[
    [],
    datetime,
]


class DecisionMemoryService:
    def __init__(
        self,
        *,
        repository: (
            DecisionMemoryRepository
        ),
        now_provider: (
            NowProvider | None
        ) = None,
    ) -> None:
        self._repository = repository
        self._now_provider = (
            now_provider
            or (
                lambda: datetime.now(
                    timezone.utc
                )
            )
        )

    def initialize(
        self,
    ) -> None:
        self._repository.initialize()

    def capture_report(
        self,
        *,
        report: (
            InvestmentThesisReport
        ),
    ) -> DecisionMemoryCaptureResult:
        captured: list[
            DecisionMemoryRecord
        ] = []
        duplicate_count = 0

        for thesis in report.theses:
            record = self._record(
                thesis=thesis
            )

            if self._repository.save_if_new(
                record=record
            ):
                captured.append(record)
            else:
                duplicate_count += 1

        return DecisionMemoryCaptureResult(
            captured_count=len(captured),
            duplicate_count=(
                duplicate_count
            ),
            records=tuple(captured),
        )

    def recent(
        self,
        *,
        limit: int = 50,
        symbol: str | None = None,
        recommendation: (
            str | None
        ) = None,
    ) -> tuple[
        DecisionMemoryRecord,
        ...
    ]:
        return self._repository.list_recent(
            limit=limit,
            symbol=symbol,
            recommendation=(
                recommendation
            ),
        )

    def overview(
        self,
        *,
        limit: int = 10,
    ) -> DecisionMemoryOverview:
        return DecisionMemoryOverview(
            generated_at=self._utc_now(),
            total_count=(
                self._repository
                .count_all()
            ),
            executable_count=(
                self._repository
                .count_executable()
            ),
            executed_count=(
                self._repository
                .count_executed()
            ),
            symbol_count=(
                self._repository
                .count_symbols()
            ),
            latest=(
                self._repository
                .list_recent(
                    limit=limit
                )
            ),
        )

    def _record(
        self,
        *,
        thesis: InvestmentThesis,
    ) -> DecisionMemoryRecord:
        captured_at = self._utc_now()
        capabilities = tuple(
            DecisionMemoryCapability(
                capability=(
                    item.capability
                ),
                status=item.status,
                score=item.score,
                maximum=item.maximum,
                confidence=(
                    item.confidence
                ),
                stance=item.stance,
                summary=item.summary,
                evidence=item.evidence,
                blockers=item.blockers,
            )
            for item
            in thesis.capabilities
        )

        fingerprint = (
            self._fingerprint(
                thesis=thesis,
                capabilities=capabilities,
            )
        )

        return DecisionMemoryRecord(
            decision_id=(
                f"KAIRO-{captured_at:%Y}-"
                f"{uuid4().hex[:12].upper()}"
            ),
            fingerprint=fingerprint,
            captured_at=captured_at,
            thesis_generated_at=(
                thesis.generated_at
            ),
            symbol=thesis.symbol,
            recommendation=(
                thesis.recommendation
            ),
            score=thesis.score,
            confidence=(
                thesis.confidence
            ),
            confidence_coverage=(
                thesis
                .confidence_coverage
            ),
            risk_tier=thesis.risk_tier,
            time_horizon=(
                thesis.time_horizon
            ),
            suggested_position_value=(
                thesis
                .suggested_position_value
            ),
            eligible_for_execution=(
                thesis
                .eligible_for_execution
            ),
            headline=thesis.headline,
            primary_driver=(
                thesis.primary_driver
            ),
            capabilities=capabilities,
            reasons=thesis.reasons,
            blockers=thesis.blockers,
            warnings=thesis.warnings,
            executed=False,
            paper_trade_id=None,
        )

    @staticmethod
    def _fingerprint(
        *,
        thesis: InvestmentThesis,
        capabilities: tuple[
            DecisionMemoryCapability,
            ...
        ],
    ) -> str:
        payload = {
            "symbol": thesis.symbol,
            "recommendation": (
                thesis.recommendation
            ),
            "score": thesis.score,
            "confidence": (
                thesis.confidence
            ),
            "confidence_coverage": (
                thesis
                .confidence_coverage
            ),
            "risk_tier": (
                thesis.risk_tier
            ),
            "time_horizon": (
                thesis.time_horizon
            ),
            "suggested_position_value": (
                thesis
                .suggested_position_value
            ),
            "eligible_for_execution": (
                thesis
                .eligible_for_execution
            ),
            "headline": thesis.headline,
            "primary_driver": (
                thesis.primary_driver
            ),
            "capabilities": [
                item.to_dictionary()
                for item in capabilities
            ],
            "reasons": list(
                thesis.reasons
            ),
            "blockers": list(
                thesis.blockers
            ),
            "warnings": list(
                thesis.warnings
            ),
        }

        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(
            encoded
        ).hexdigest()

    def _utc_now(
        self,
    ) -> datetime:
        value = self._now_provider()

        if value.tzinfo is None:
            raise ValueError(
                "Decision Memory clock "
                "must be timezone-aware."
            )

        return value.astimezone(
            timezone.utc
        )
