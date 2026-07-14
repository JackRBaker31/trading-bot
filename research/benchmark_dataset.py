from __future__ import annotations

import json
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VALID_CATEGORIES = {
    "analyst",
    "dividends",
    "earnings",
    "guidance",
    "litigation",
    "m_and_a",
    "macro",
    "misc",
    "products",
    "regulation",
}

VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_STATUSES = {"draft", "ready"}
VALID_IMPACT_TERMS = {"SHORTTERM", "LONGTERM"}
VALID_IMPACT_SCOPES = {"GLOBAL", "INDUSTRY", "STOCK"}
VALID_SENTIMENTS = {"POSITIVE", "NEGATIVE", "NEUTRAL"}


@dataclass(frozen=True)
class BenchmarkMigrationResult:
    migrated_count: int
    skipped_count: int
    created_article_paths: tuple[Path, ...]
    created_label_paths: tuple[Path, ...]
    backup_paths: tuple[Path, ...]
    messages: tuple[str, ...]


@dataclass(frozen=True)
class BenchmarkArticle:
    benchmark_id: str
    status: str
    headline: str
    source: str
    category: str
    sector: str
    company: str
    ticker: str
    difficulty: str
    published_at: str
    article_text: str


@dataclass(frozen=True)
class BenchmarkLabel:
    benchmark_id: str
    impact_term: str
    impact_scope: str
    scope_items: tuple[str, ...]
    highlights: tuple[str, ...]
    sentiment: str


@dataclass(frozen=True)
class BenchmarkDatasetStatistics:
    article_count: int
    label_count: int
    categories: dict[str, int]
    sources: dict[str, int]
    sectors: dict[str, int]
    companies: dict[str, int]
    difficulties: dict[str, int]


@dataclass(frozen=True)
class BenchmarkValidationResult:
    approved: bool
    errors: tuple[str, ...]


class BenchmarkDataset:
    def __init__(
        self,
        *,
        articles_directory: Path,
        labels_directory: Path,
    ) -> None:
        self.articles_directory = Path(articles_directory)
        self.labels_directory = Path(labels_directory)
        self.articles: dict[str, BenchmarkArticle] = {}
        self.labels: dict[str, BenchmarkLabel] = {}

    def load(self) -> None:
        self.articles = self._load_articles()
        self.labels = self._load_labels()

    def validate(
        self,
    ) -> BenchmarkValidationResult:
        errors: list[str] = []

        ready_article_ids = set(
            self.ready_articles
        )

        all_article_ids = set(
            self.articles
        )

        label_ids = set(
            self.labels
        )

        for benchmark_id in sorted(
            ready_article_ids - label_ids
        ):
            errors.append(
                f"Missing label for {benchmark_id}."
            )

        for benchmark_id in sorted(
            label_ids - all_article_ids
        ):
            errors.append(
                f"Missing article for {benchmark_id}."
            )

        for article in self.articles.values():
            errors.extend(
                self._validate_article(
                    article
                )
            )

        for benchmark_id, label in (
            self.labels.items()
        ):
            article = self.articles.get(
                benchmark_id
            )

            if (
                article is not None
                and article.status == "draft"
            ):
                continue

            errors.extend(
                self._validate_label(
                    label
                )
            )

        return BenchmarkValidationResult(
            approved=not errors,
            errors=tuple(errors),
        )

    def statistics(self) -> BenchmarkDatasetStatistics:
        return BenchmarkDatasetStatistics(
            article_count=len(self.articles),
            label_count=len(self.labels),
            categories=self._count_values(
                article.category for article in self.articles.values()
            ),
            sources=self._count_values(
                article.source for article in self.articles.values()
            ),
            sectors=self._count_values(
                article.sector for article in self.articles.values()
            ),
            companies=self._count_values(
                article.company
                for article in self.articles.values()
                if article.company
            ),
            difficulties=self._count_values(
                article.difficulty for article in self.articles.values()
            ),
        )

    def next_benchmark_id(self) -> str:
        """Return the first unused BENCH-XXXX identifier."""
        return self._next_available_id(set(self.articles) | set(self.labels))

    def create_templates(self) -> tuple[Path, Path]:
        self.articles_directory.mkdir(parents=True, exist_ok=True)
        self.labels_directory.mkdir(parents=True, exist_ok=True)

        # Include IDs already present on disk, even if load() has not been called.
        reserved_ids = set(self.articles) | set(self.labels)
        reserved_ids.update(self._collect_ids_from_directory(self.articles_directory))
        reserved_ids.update(self._collect_ids_from_directory(self.labels_directory))
        benchmark_id = self._next_available_id(reserved_ids)

        article_path = self.articles_directory / f"{benchmark_id}.json"
        label_path = self.labels_directory / f"{benchmark_id}.json"

        article_data = {
            "benchmark_id": benchmark_id,
            "status": "draft",
            "headline": "",
            "source": "",
            "category": "misc",
            "sector": "",
            "company": "",
            "ticker": "",
            "difficulty": "medium",
            "published_at": "",
            "article_text": "",
        }
        label_data = {
            "benchmark_id": benchmark_id,
            "impact_term": "SHORTTERM",
            "impact_scope": "STOCK",
            "scope_items": [],
            "highlights": [],
            "sentiment": "NEUTRAL",
        }

        self._write_json_exclusive(article_path, article_data)
        try:
            self._write_json_exclusive(label_path, label_data)
        except Exception:
            article_path.unlink(missing_ok=True)
            raise

        return article_path, label_path

    def migrate_legacy_articles(
        self,
        *,
        backup_directory: Path,
    ) -> BenchmarkMigrationResult:
        self.articles_directory.mkdir(parents=True, exist_ok=True)
        self.labels_directory.mkdir(parents=True, exist_ok=True)
        backup_directory = Path(backup_directory)
        backup_directory.mkdir(parents=True, exist_ok=True)

        created_article_paths: list[Path] = []
        created_label_paths: list[Path] = []
        backup_paths: list[Path] = []
        messages: list[str] = []
        migrated_count = 0
        skipped_count = 0

        reserved_ids = set(self.articles) | set(self.labels)
        reserved_ids.update(self._collect_ids_from_directory(self.articles_directory))
        reserved_ids.update(self._collect_ids_from_directory(self.labels_directory))

        for file_path in sorted(self.articles_directory.glob("*.json")):
            data = self._load_json_object(file_path)

            if "benchmark_id" in data:
                skipped_count += 1
                messages.append(f"Skipped current-schema file: {file_path.name}")
                continue

            if "article_id" not in data:
                skipped_count += 1
                messages.append(f"Skipped unrecognised file: {file_path.name}")
                continue

            benchmark_id = self._next_available_id(reserved_ids)
            reserved_ids.add(benchmark_id)

            allowed_symbols = data.get("allowed_symbols", [])
            if not isinstance(allowed_symbols, list):
                raise ValueError(
                    f"Legacy allowed_symbols must be a list: {file_path}"
                )

            cleaned_symbols = self._normalise_string_list(
                allowed_symbols,
                uppercase=True,
            )
            ticker = cleaned_symbols[0] if len(cleaned_symbols) == 1 else ""

            article_data = {
                "benchmark_id": benchmark_id,
                "headline": str(data.get("headline", "")).strip(),
                "source": str(data.get("source", "")).strip(),
                "category": "misc",
                "sector": "",
                "company": "",
                "ticker": ticker,
                "difficulty": "medium",
                "published_at": "",
                "article_text": str(data.get("article_text", "")).strip(),
            }
            label_data = {
                "benchmark_id": benchmark_id,
                "impact_term": "SHORTTERM",
                "impact_scope": "STOCK" if cleaned_symbols else "GLOBAL",
                "scope_items": cleaned_symbols,
                "highlights": [],
                "sentiment": "NEUTRAL",
            }

            new_article_path = self.articles_directory / f"{benchmark_id}.json"
            new_label_path = self.labels_directory / f"{benchmark_id}.json"
            backup_path = backup_directory / file_path.name

            for target in (new_article_path, new_label_path, backup_path):
                if target.exists():
                    raise FileExistsError(
                        f"Migration target already exists: {target}"
                    )

            self._write_json_exclusive(new_article_path, article_data)
            try:
                self._write_json_exclusive(new_label_path, label_data)
                shutil.move(str(file_path), str(backup_path))
            except Exception:
                new_article_path.unlink(missing_ok=True)
                new_label_path.unlink(missing_ok=True)
                raise

            migrated_count += 1
            created_article_paths.append(new_article_path)
            created_label_paths.append(new_label_path)
            backup_paths.append(backup_path)
            messages.append(f"Migrated {file_path.name} to {benchmark_id}.")

        # Keep the in-memory view synchronized with the migrated files.
        self.load()

        return BenchmarkMigrationResult(
            migrated_count=migrated_count,
            skipped_count=skipped_count,
            created_article_paths=tuple(created_article_paths),
            created_label_paths=tuple(created_label_paths),
            backup_paths=tuple(backup_paths),
            messages=tuple(messages),
        )

    def _load_articles(self) -> dict[str, BenchmarkArticle]:
        articles: dict[str, BenchmarkArticle] = {}
        if not self.articles_directory.exists():
            return articles

        for file_path in sorted(self.articles_directory.glob("*.json")):
            data = self._load_json_object(file_path)
            try:
                article = BenchmarkArticle(
                    benchmark_id=str(
                        data["benchmark_id"]
                    ).strip(),
                    status=str(
                        data.get(
                            "status",
                            "ready",
                        )
                    ).lower().strip(),
                    headline=str(
                        data["headline"]
                    ).strip(),
                    source=str(
                        data["source"]
                    ).strip(),
                    category=str(
                        data["category"]
                    ).lower().strip(),
                    sector=str(
                        data["sector"]
                    ).strip(),
                    company=str(
                        data["company"]
                    ).strip(),
                    ticker=str(
                        data["ticker"]
                    ).upper().strip(),
                    difficulty=str(
                        data["difficulty"]
                    ).lower().strip(),
                    published_at=str(
                        data["published_at"]
                    ).strip(),
                    article_text=str(
                        data["article_text"]
                    ).strip(),
                )
            except (KeyError, TypeError) as error:
                raise ValueError(
                    f"Article did not match the required schema: {file_path}"
                ) from error

            if article.benchmark_id in articles:
                raise ValueError(
                    f"Duplicate article benchmark ID: {article.benchmark_id}"
                )
            articles[article.benchmark_id] = article

        return articles

    def _load_labels(self) -> dict[str, BenchmarkLabel]:
        labels: dict[str, BenchmarkLabel] = {}
        if not self.labels_directory.exists():
            return labels

        for file_path in sorted(self.labels_directory.glob("*.json")):
            data = self._load_json_object(file_path)
            try:
                scope_items = data["scope_items"]
                highlights = data["highlights"]
                if not isinstance(scope_items, list):
                    raise TypeError("scope_items must be a list")
                if not isinstance(highlights, list):
                    raise TypeError("highlights must be a list")

                label = BenchmarkLabel(
                    benchmark_id=self._required_string(data, "benchmark_id"),
                    impact_term=self._required_string(data, "impact_term").upper(),
                    impact_scope=self._required_string(data, "impact_scope").upper(),
                    scope_items=tuple(
                        self._normalise_string_list(scope_items, uppercase=True)
                    ),
                    highlights=tuple(
                        self._normalise_string_list(highlights, uppercase=False)
                    ),
                    sentiment=self._required_string(data, "sentiment").upper(),
                )
            except (KeyError, TypeError) as error:
                raise ValueError(
                    f"Label did not match the required schema: {file_path}"
                ) from error

            if label.benchmark_id in labels:
                raise ValueError(
                    f"Duplicate label benchmark ID: {label.benchmark_id}"
                )
            labels[label.benchmark_id] = label

        return labels

    @staticmethod
    def _count_values(values: Any) -> dict[str, int]:
        return dict(sorted(Counter(values).items()))

    @staticmethod
    def _next_available_id(reserved_ids: set[str]) -> str:
        number = 1
        while True:
            candidate = f"BENCH-{number:04d}"
            if candidate not in reserved_ids:
                return candidate
            number += 1

    @classmethod
    def _collect_ids_from_directory(cls, directory: Path) -> set[str]:
        ids: set[str] = set()
        if not directory.exists():
            return ids

        for file_path in directory.glob("*.json"):
            try:
                data = cls._load_json_object(file_path)
            except ValueError:
                continue
            benchmark_id = data.get("benchmark_id")
            if isinstance(benchmark_id, str) and benchmark_id.strip():
                ids.add(benchmark_id.strip())
        return ids

    @staticmethod
    def _required_string(data: dict[str, object], key: str) -> str:
        value = data[key]
        if not isinstance(value, str):
            raise TypeError(f"{key} must be a string")
        return value.strip()

    @staticmethod
    def _normalise_string_list(
        values: list[object],
        *,
        uppercase: bool,
    ) -> list[str]:
        result: list[str] = []
        for value in values:
            text = str(value).strip()
            if not text:
                continue
            result.append(text.upper() if uppercase else text)
        return result

    @staticmethod
    def _write_json_exclusive(file_path: Path, data: dict[str, object]) -> None:
        payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        with file_path.open("x", encoding="utf-8") as file:
            file.write(payload)

    @staticmethod
    def _load_json_object(file_path: Path) -> dict[str, object]:
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except OSError as error:
            raise ValueError(f"Could not read JSON file: {file_path}") from error
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON: {file_path}") from error

        if not isinstance(data, dict):
            raise ValueError(
                f"Benchmark file must contain a JSON object: {file_path}"
            )
        return data

    @staticmethod
    def _validate_article(article: BenchmarkArticle) -> list[str]:
        errors: list[str] = []

        if article.status not in VALID_STATUSES:
            errors.append(
                f"{article.benchmark_id}: "
                f"invalid status {article.status}."
            )

            return errors

        if article.status == "draft":
            return errors

        if not article.benchmark_id:
            errors.append("Article benchmark ID is empty.")
        elif not BenchmarkDataset._is_valid_benchmark_id(article.benchmark_id):
            errors.append(f"Invalid benchmark ID: {article.benchmark_id}.")

        if not article.headline:
            errors.append(f"{article.benchmark_id}: headline is required.")
        if not article.source:
            errors.append(f"{article.benchmark_id}: source is required.")
        if article.category not in VALID_CATEGORIES:
            errors.append(
                f"{article.benchmark_id}: invalid category {article.category}."
            )
        if article.difficulty not in VALID_DIFFICULTIES:
            errors.append(
                f"{article.benchmark_id}: invalid difficulty {article.difficulty}."
            )
        if not article.article_text:
            errors.append(f"{article.benchmark_id}: article text is required.")

        return errors

    @staticmethod
    def _validate_label(label: BenchmarkLabel) -> list[str]:
        errors: list[str] = []

        if not BenchmarkDataset._is_valid_benchmark_id(label.benchmark_id):
            errors.append(f"Invalid benchmark ID: {label.benchmark_id}.")
        if label.impact_term not in VALID_IMPACT_TERMS:
            errors.append(f"{label.benchmark_id}: invalid impact term.")
        if label.impact_scope not in VALID_IMPACT_SCOPES:
            errors.append(f"{label.benchmark_id}: invalid impact scope.")
        if label.sentiment not in VALID_SENTIMENTS:
            errors.append(f"{label.benchmark_id}: invalid sentiment.")
        if label.impact_scope == "STOCK" and not label.scope_items:
            errors.append(
                f"{label.benchmark_id}: STOCK impact scope requires scope_items."
            )

        return errors

    @staticmethod
    def _is_valid_benchmark_id(benchmark_id: str) -> bool:
        prefix = "BENCH-"
        return (
            benchmark_id.startswith(prefix)
            and len(benchmark_id) == len(prefix) + 4
            and benchmark_id[len(prefix):].isdigit()
        )

    @property
    def ready_articles(
        self,
    ) -> dict[str, BenchmarkArticle]:
        return {
            benchmark_id: article
            for benchmark_id, article
            in self.articles.items()
            if article.status == "ready"
        }


    @property
    def draft_articles(
        self,
    ) -> dict[str, BenchmarkArticle]:
        return {
            benchmark_id: article
            for benchmark_id, article
            in self.articles.items()
            if article.status == "draft"
        }
