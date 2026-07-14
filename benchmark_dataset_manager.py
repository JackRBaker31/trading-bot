import argparse
import json

from pathlib import Path

from research.benchmark_dataset import (
    BenchmarkDataset,
)


ARTICLES_DIRECTORY = Path(
    "research/articles"
)
LABELS_DIRECTORY = Path(
    "research/labels"
)
BACKUP_DIRECTORY = Path(
    "research/legacy_backup"
)


def create_dataset() -> BenchmarkDataset:
    dataset = BenchmarkDataset(
        articles_directory=(
            ARTICLES_DIRECTORY
        ),
        labels_directory=(
            LABELS_DIRECTORY
        ),
    )

    dataset.load()

    return dataset


def create_templates() -> None:
    dataset = create_dataset()

    article_path, label_path = (
        dataset.create_templates()
    )

    print()
    print("Benchmark templates created.")
    print(f"Article: {article_path}")
    print(f"Label:   {label_path}")


def validate_dataset() -> None:
    dataset = create_dataset()
    result = dataset.validate()

    print()
    print("BENCHMARK DATASET VALIDATION")
    print("=" * 50)

    if result.approved:
        print("Dataset is valid.")
        return

    print(
        f"Dataset has "
        f"{len(result.errors)} error(s):"
    )

    for error in result.errors:
        print(f"- {error}")

    raise SystemExit(1)


def display_statistics() -> None:
    dataset = create_dataset()
    statistics = dataset.statistics()

    print()
    print("BENCHMARK DATASET STATISTICS")
    print("=" * 50)
    print(
        f"Articles: "
        f"{statistics.article_count}"
    )
    print(
        f"Labels:   "
        f"{statistics.label_count}"
    )
    print(
        f"Ready:    "
        f"{len(dataset.ready_articles)}"
    )
    print(
        f"Drafts:   "
        f"{len(dataset.draft_articles)}"
    )

    sections = {
        "Categories": statistics.categories,
        "Sources": statistics.sources,
        "Sectors": statistics.sectors,
        "Companies": statistics.companies,
        "Difficulties": (
            statistics.difficulties
        ),
    }

    for title, values in sections.items():
        print()
        print(title)

        if not values:
            print("- None")
            continue

        for name, count in values.items():
            print(f"- {name}: {count}")

def migrate_dataset() -> None:
    dataset = BenchmarkDataset(
        articles_directory=ARTICLES_DIRECTORY,
        labels_directory=LABELS_DIRECTORY,
    )

    result = dataset.migrate_legacy_articles(
        backup_directory=BACKUP_DIRECTORY,
    )

    print()
    print("BENCHMARK DATASET MIGRATION")
    print("=" * 50)
    print(f"Migrated: {result.migrated_count}")
    print(f"Skipped:  {result.skipped_count}")

    for message in result.messages:
        print(f"- {message}")

    if result.migrated_count:
        print()
        print("Legacy files were backed up to:")
        print(BACKUP_DIRECTORY)
        print()
        print(
            "Review and complete the generated "
            "article metadata and labels before "
            "running validation."
        )

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Manage the financial-news "
            "benchmark dataset."
        )
    )

    parser.add_argument(
        "command",
        choices=[
            "stats",
            "validate",
            "migrate",
            "create",
            "ready",
            "draft",
        ]
    )

    parser.add_argument(
        "benchmark_id",
        nargs="?",
    )

    return parser.parse_args()

def promote_ready(
    benchmark_id: str,
) -> None:
    cleaned_benchmark_id = (
        benchmark_id.upper().strip()
    )

    dataset = create_dataset()

    article = dataset.articles.get(
        cleaned_benchmark_id
    )

    if article is None:
        raise SystemExit(
            f"{cleaned_benchmark_id} not found."
        )

    path = (
        ARTICLES_DIRECTORY
        / f"{cleaned_benchmark_id}.json"
    )

    data = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    original_status = str(
        data.get("status", "draft")
    )

    data["status"] = "ready"

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    dataset = create_dataset()
    validation = dataset.validate()

    relevant_errors = tuple(
        error
        for error in validation.errors
        if cleaned_benchmark_id in error
    )

    if relevant_errors:
        data["status"] = original_status

        path.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        print()
        print("Promotion failed.")
        print()

        for error in relevant_errors:
            print(f"- {error}")

        raise SystemExit(1)

    print()
    print("BENCHMARK PROMOTED")
    print("=" * 50)
    print(
        f"{cleaned_benchmark_id} is READY."
    )

def promote_draft(
    benchmark_id: str,
) -> None:
    cleaned_benchmark_id = (
        benchmark_id.upper().strip()
    )

    path = (
        ARTICLES_DIRECTORY
        / f"{cleaned_benchmark_id}.json"
    )

    if not path.exists():
        raise SystemExit(
            f"{cleaned_benchmark_id} not found."
        )

    data = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    data["status"] = "draft"

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("BENCHMARK RETURNED TO DRAFT")
    print("=" * 50)
    print(
        f"{cleaned_benchmark_id} is now DRAFT."
    )

def main() -> None:
    args = parse_args()

    if args.command == "create":
        create_templates()
    elif args.command == "migrate":
        migrate_dataset()
    elif args.command == "validate":
        validate_dataset()
    elif args.command == "stats":
        display_statistics()
    elif args.command == "ready":
        if args.benchmark_id is None:
            raise SystemExit(
                "Benchmark ID required."
            )

        promote_ready(
            args.benchmark_id
        )

    elif args.command == "draft":
        if args.benchmark_id is None:
            raise SystemExit(
                "Benchmark ID required."
            )

        promote_draft(
            args.benchmark_id
        )

if __name__ == "__main__":
    main()

def migrate_dataset() -> None:
    dataset = BenchmarkDataset(
        articles_directory=(
            ARTICLES_DIRECTORY
        ),
        labels_directory=(
            LABELS_DIRECTORY
        ),
    )

    result = dataset.migrate_legacy_articles(
        backup_directory=(
            BACKUP_DIRECTORY
        )
    )

    print()
    print("BENCHMARK DATASET MIGRATION")
    print("=" * 50)
    print(
        f"Migrated: {result.migrated_count}"
    )
    print(
        f"Skipped:  {result.skipped_count}"
    )

    for message in result.messages:
        print(f"- {message}")

    if result.migrated_count:
        print()
        print(
            "Legacy files were backed up to:"
        )
        print(BACKUP_DIRECTORY)
        print()
        print(
            "Review and complete the generated "
            "article metadata and labels before "
            "running validation."
        )