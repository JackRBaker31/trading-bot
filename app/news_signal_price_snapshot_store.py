import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from app.news_signal_price_snapshot import (
    NewsSignalPriceSnapshot,
)


class NewsSignalPriceSnapshotStore:
    def __init__(
        self,
        file_path: str = (
            "data/news_signal_price_snapshots.jsonl"
        ),
    ) -> None:
        self.file_path = Path(
            file_path
        )

    def append(
        self,
        *,
        snapshot: NewsSignalPriceSnapshot,
    ) -> None:
        if self.get_by_article_id(
            snapshot.article_id
        ) is not None:
            raise ValueError(
                "A price snapshot already exists "
                "for this article."
            )

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
                    snapshot
                ),
                file,
            )
            file.write("\n")

    def load_all(
        self,
    ) -> list[NewsSignalPriceSnapshot]:
        if not self.file_path.exists():
            return []

        snapshots: list[
            NewsSignalPriceSnapshot
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
                    snapshots.append(
                        self._from_dictionary(
                            json.loads(cleaned)
                        )
                    )
                except (
                    KeyError,
                    TypeError,
                    ValueError,
                    json.JSONDecodeError,
                ) as error:
                    raise ValueError(
                        "Invalid news signal price "
                        f"snapshot at line "
                        f"{line_number}."
                    ) from error

        return snapshots

    def get_by_article_id(
        self,
        article_id: str,
    ) -> NewsSignalPriceSnapshot | None:
        cleaned_article_id = (
            article_id.strip()
        )

        for snapshot in self.load_all():
            if (
                snapshot.article_id
                == cleaned_article_id
            ):
                return snapshot

        return None

    @staticmethod
    def _to_dictionary(
        snapshot: NewsSignalPriceSnapshot,
    ) -> dict[str, object]:
        payload = asdict(snapshot)
        payload["captured_at"] = (
            snapshot.captured_at.isoformat()
        )
        return payload

    @staticmethod
    def _from_dictionary(
        payload: dict[str, object],
    ) -> NewsSignalPriceSnapshot:
        return NewsSignalPriceSnapshot(
            article_id=str(
                payload["article_id"]
            ),
            symbol=str(
                payload["symbol"]
            ),
            captured_at=datetime.fromisoformat(
                str(payload["captured_at"])
            ),
            price=float(
                payload["price"]
            ),
            provider=str(
                payload["provider"]
            ),
        )