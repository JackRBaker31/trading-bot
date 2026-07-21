import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from app.news_signal import NewsSignal


class NewsSignalStore:
    def __init__(
        self,
        file_path: str = (
            "data/news_signals.jsonl"
        ),
    ) -> None:
        self.file_path = Path(
            file_path
        )

    def append(
        self,
        *,
        signal: NewsSignal,
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
                    signal
                ),
                file,
            )
            file.write("\n")

    def load_all(
        self,
    ) -> list[NewsSignal]:
        if not self.file_path.exists():
            return []

        signals: list[
            NewsSignal
        ] = []

        with self.file_path.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            for line_number, line in enumerate(
                file,
                start=1,
            ):
                cleaned_line = line.strip()

                if not cleaned_line:
                    continue

                try:
                    payload = json.loads(
                        cleaned_line
                    )
                    signals.append(
                        self._from_dictionary(
                            payload
                        )
                    )
                except (
                    KeyError,
                    TypeError,
                    ValueError,
                    json.JSONDecodeError,
                ) as error:
                    raise ValueError(
                        "Invalid news signal record "
                        f"at line {line_number}."
                    ) from error

        return signals

    @staticmethod
    def _to_dictionary(
        signal: NewsSignal,
    ) -> dict[str, object]:
        payload = asdict(
            signal
        )
        payload["published_at"] = (
            signal.published_at
            .isoformat()
        )
        payload["expires_at"] = (
            signal.expires_at
            .isoformat()
        )
        return payload

    @staticmethod
    def _from_dictionary(
        payload: dict[str, object],
    ) -> NewsSignal:
        return NewsSignal(
            article_id=str(
                payload["article_id"]
            ),
            symbol=str(
                payload["symbol"]
            ),
            headline=str(
                payload["headline"]
            ),
            sentiment=float(
                payload["sentiment"]
            ),
            relevance=float(
                payload["relevance"]
            ),
            confidence=float(
                payload["confidence"]
            ),
            event_type=str(
                payload["event_type"]
            ),
            is_material=bool(
                payload["is_material"]
            ),
            published_at=datetime.fromisoformat(
                str(
                    payload["published_at"]
                )
            ),
            expires_at=datetime.fromisoformat(
                str(
                    payload["expires_at"]
                )
            ),
            source=str(
                payload["source"]
            ),
            reasoning_summary=str(
                payload["reasoning_summary"]
            ),
        )