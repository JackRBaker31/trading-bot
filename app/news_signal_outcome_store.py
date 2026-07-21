import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from app.news_signal_outcome import (
    NewsSignalOutcome,
)


class NewsSignalOutcomeStore:
    def __init__(
        self,
        file_path: str = (
            "data/news_signal_outcomes.jsonl"
        ),
    ) -> None:
        self.file_path = Path(
            file_path
        )

    def append(
        self,
        *,
        outcome: NewsSignalOutcome,
    ) -> None:
        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.file_path.open(
            mode="a",
            encoding="utf-8",
        ) as file:
            json.dump(
                self._to_dictionary(
                    outcome
                ),
                file,
            )
            file.write("\n")

    def load_all(
        self,
    ) -> list[NewsSignalOutcome]:
        if not self.file_path.exists():
            return []

        outcomes: list[
            NewsSignalOutcome
        ] = []

        with self.file_path.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            for line_number, line in enumerate(
                file,
                start=1,
            ):
                cleaned = line.strip()

                if not cleaned:
                    continue

                try:
                    outcomes.append(
                        self._from_dictionary(
                            json.loads(
                                cleaned
                            )
                        )
                    )
                except (
                    KeyError,
                    TypeError,
                    ValueError,
                    json.JSONDecodeError,
                ) as error:
                    raise ValueError(
                        "Invalid news signal "
                        f"outcome at line "
                        f"{line_number}."
                    ) from error

        return outcomes

    @staticmethod
    def _to_dictionary(
        outcome: NewsSignalOutcome,
    ) -> dict[str, object]:
        payload = asdict(
            outcome
        )
        payload[
            "signal_published_at"
        ] = (
            outcome.signal_published_at
            .isoformat()
        )
        payload["observed_at"] = (
            outcome.observed_at.isoformat()
        )
        return payload

    @staticmethod
    def _from_dictionary(
        payload: dict[str, object],
    ) -> NewsSignalOutcome:
        return NewsSignalOutcome(
            article_id=str(
                payload["article_id"]
            ),
            symbol=str(
                payload["symbol"]
            ),
            horizon_name=str(
                payload["horizon_name"]
            ),
            signal_published_at=(
                datetime.fromisoformat(
                    str(
                        payload[
                            "signal_published_at"
                        ]
                    )
                )
            ),
            observed_at=(
                datetime.fromisoformat(
                    str(
                        payload["observed_at"]
                    )
                )
            ),
            reference_price=float(
                payload["reference_price"]
            ),
            observed_price=float(
                payload["observed_price"]
            ),
            return_percent=float(
                payload["return_percent"]
            ),
        )