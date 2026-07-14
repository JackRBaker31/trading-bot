import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.news_analysis import NewsAnalysis


@dataclass(frozen=True)
class NewsJournalEntry:
    timestamp: datetime
    article_id: str
    headline: str
    source: str
    article_text: str
    analysis: NewsAnalysis

    def to_dictionary(self) -> dict[str, object]:
        data = asdict(self)

        data["timestamp"] = (
            self.timestamp
            .astimezone(timezone.utc)
            .isoformat()
        )

        analysis = data["analysis"]

        if not isinstance(analysis, dict):
            raise TypeError(
                "News analysis must serialize "
                "to an object."
            )

        analysis["impact_term"] = (
            self.analysis.impact_term.value
        )
        analysis["impact_scope"] = (
            self.analysis.impact_scope.value
        )
        analysis["sentiment"] = (
            self.analysis.sentiment.value
        )
        analysis["scope_items"] = list(
            self.analysis.scope_items
        )
        analysis["highlights"] = list(
            self.analysis.highlights
        )

        return data


class NewsJournal:
    def __init__(
        self,
        file_path: str = (
            "data/news_journal.jsonl"
        ),
    ) -> None:
        self.file_path = Path(
            file_path
        )

    def record(
        self,
        entry: NewsJournalEntry,
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
                entry.to_dictionary(),
                file,
                ensure_ascii=False,
            )
            file.write("\n")