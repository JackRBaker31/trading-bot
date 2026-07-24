from statistics import pstdev
from typing import Any, Mapping

from app.adaptive_intelligence_models import (
    CommitteeVote,
    InvestmentCommitteeDecision,
)


class InvestmentCommitteeService:
    def deliberate(
        self,
        *,
        theses: tuple[
            Mapping[str, Any],
            ...
        ],
    ) -> tuple[
        InvestmentCommitteeDecision,
        ...
    ]:
        decisions: list[
            InvestmentCommitteeDecision
        ] = []

        for thesis in theses:
            votes = tuple(
                self._vote(
                    capability=capability
                )
                for capability
                in thesis.get(
                    "capabilities",
                    (),
                )
            )

            numeric = [
                float(vote.score)
                / self._maximum(
                    thesis=thesis,
                    agent=vote.agent,
                )
                for vote in votes
                if vote.score is not None
            ]

            consensus = (
                sum(numeric) / len(numeric)
                if numeric
                else 0.0
            )
            disagreement = (
                pstdev(numeric)
                if len(numeric) >= 2
                else 0.0
            )
            confidence = (
                sum(
                    vote.confidence
                    for vote in votes
                )
                / len(votes)
                if votes
                else 0.0
            )

            blockers = tuple(
                str(value)
                for value
                in thesis.get(
                    "blockers",
                    (),
                )
            )

            final_stance = (
                "BLOCKED"
                if blockers
                else "BUY"
                if (
                    consensus >= 0.75
                    and disagreement <= 0.25
                )
                else "WATCH"
                if consensus >= 0.60
                else "HOLD"
                if consensus >= 0.45
                else "AVOID"
            )

            decisions.append(
                InvestmentCommitteeDecision(
                    symbol=str(
                        thesis["symbol"]
                    ),
                    final_stance=final_stance,
                    consensus_score=round(
                        consensus * 100,
                        2,
                    ),
                    disagreement_score=round(
                        disagreement * 100,
                        2,
                    ),
                    confidence=round(
                        confidence,
                        4,
                    ),
                    votes=votes,
                    blockers=blockers,
                    summary=(
                        f"{len(votes)} specialist capability "
                        f"vote(s) produced a {final_stance} "
                        "committee stance."
                    ),
                )
            )

        return tuple(decisions)

    @staticmethod
    def _vote(
        *,
        capability: Mapping[
            str,
            Any,
        ],
    ) -> CommitteeVote:
        status = str(
            capability.get(
                "status",
                "UNAVAILABLE",
            )
        )
        score = capability.get("score")
        maximum = float(
            capability.get(
                "maximum",
                1.0,
            )
        )
        confidence = float(
            capability.get(
                "confidence",
                0.0,
            )
            or 0.0
        )

        ratio = (
            float(score) / maximum
            if (
                score is not None
                and maximum > 0
            )
            else None
        )

        stance = (
            "UNAVAILABLE"
            if status != "AVAILABLE"
            else "BUY"
            if ratio is not None
            and ratio >= 0.75
            else "WATCH"
            if ratio is not None
            and ratio >= 0.60
            else "HOLD"
            if ratio is not None
            and ratio >= 0.45
            else "AVOID"
        )

        return CommitteeVote(
            agent=(
                str(
                    capability.get(
                        "capability",
                        "UNKNOWN",
                    )
                )
                + "_AGENT"
            ),
            stance=stance,
            confidence=round(
                confidence,
                4,
            ),
            score=(
                float(score)
                if score is not None
                else None
            ),
            summary=str(
                capability.get(
                    "summary",
                    "",
                )
            ),
            evidence=tuple(
                str(value)
                for value
                in capability.get(
                    "evidence",
                    (),
                )
            ),
        )

    @staticmethod
    def _maximum(
        *,
        thesis: Mapping[str, Any],
        agent: str,
    ) -> float:
        capability_name = agent.removesuffix(
            "_AGENT"
        )
        for capability in thesis.get(
            "capabilities",
            (),
        ):
            if str(
                capability.get(
                    "capability"
                )
            ) == capability_name:
                return max(
                    float(
                        capability.get(
                            "maximum",
                            1.0,
                        )
                    ),
                    0.01,
                )
        return 1.0
