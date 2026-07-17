import json
from pathlib import Path

from app.news_analysis import (
    NewsSentiment,
)
from app.news_policy_observation import (
    NewsPolicyObservation,
)
from app.orders import (
    OrderSide,
)


class NewsPolicyObservationLog:
    def __init__(
        self,
        *,
        file_path: str | Path,
    ) -> None:
        self._file_path = Path(
            file_path
        )

        self._file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def append(
        self,
        observation: NewsPolicyObservation,
    ) -> None:
        payload = {
            "symbol": observation.symbol,
            "side": observation.side.value,
            "quantity": observation.quantity,
            "analysis_available": (
                observation.analysis_available
            ),
            "analysis_sentiment": (
                observation.analysis_sentiment.value
                if observation.analysis_sentiment
                is not None
                else None
            ),
            "analysis_expires_at": (
                observation.analysis_expires_at
                .isoformat()
                if observation.analysis_expires_at
                is not None
                else None
            ),
            "would_approve": (
                observation.would_approve
            ),
            "reason": observation.reason,
            "observed_at": (
                observation.observed_at.isoformat()
            ),
        }

        with self._file_path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    payload,
                    sort_keys=True,
                )
            )
            file.write("\n")

    def read_all(
        self,
    ) -> list[NewsPolicyObservation]:
        if not self._file_path.exists():
            return []

        observations: list[
            NewsPolicyObservation
        ] = []

        with self._file_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            for line in file:
                stripped_line = line.strip()

                if not stripped_line:
                    continue

                payload = json.loads(
                    stripped_line
                )

                sentiment_value = payload[
                    "analysis_sentiment"
                ]

                expiry_value = payload[
                    "analysis_expires_at"
                ]

                observations.append(
                    NewsPolicyObservation(
                        symbol=payload["symbol"],
                        side=OrderSide(
                            payload["side"]
                        ),
                        quantity=payload["quantity"],
                        analysis_available=payload[
                            "analysis_available"
                        ],
                        analysis_sentiment=(
                            NewsSentiment(
                                sentiment_value
                            )
                            if sentiment_value
                            is not None
                            else None
                        ),
                        analysis_expires_at=(
                            __import__(
                                "datetime"
                            )
                            .datetime
                            .fromisoformat(
                                expiry_value
                            )
                            if expiry_value
                            is not None
                            else None
                        ),
                        would_approve=payload[
                            "would_approve"
                        ],
                        reason=payload["reason"],
                        observed_at=(
                            __import__(
                                "datetime"
                            )
                            .datetime
                            .fromisoformat(
                                payload[
                                    "observed_at"
                                ]
                            )
                        ),
                    )
                )

        return observations