from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

BUNDLE_ROOT = Path(__file__).resolve().parent
PAYLOAD_ROOT = BUNDLE_ROOT / "payload"

FILES = (
    "app/historical_similarity_models.py",
    "app/historical_similarity_service.py",
    "app/investment_thesis_service.py",
    "web/dependencies.py",
    "web/app.py",
    "frontend/src/hooks/useHistoricalSimilarity.ts",
    "frontend/src/components/decision/HistoricalSimilarityPanel.tsx",
    "frontend/src/pages/DecisionExplainabilityPage.tsx",
    "frontend/src/__tests__/decision-explainability.test.tsx",
    "tests/test_historical_similarity_service.py",
    "tests/test_investment_thesis_service.py",
    "tests/test_web_historical_similarity.py",
)


def locate_project_root() -> Path:
    current = Path.cwd().resolve()

    if (
        (current / "app").is_dir()
        and (current / "frontend" / "src").is_dir()
        and (current / "web").is_dir()
        and (current / "tests").is_dir()
    ):
        return current

    if (
        current.name.lower() == "frontend"
        and (current / "src").is_dir()
        and (current.parent / "app").is_dir()
        and (current.parent / "web").is_dir()
    ):
        return current.parent

    raise RuntimeError(
        "Run this installer from the trading-bot project root "
        "or its frontend folder."
    )


def validate_baseline(project_root: Path) -> None:
    required = (
        project_root / "app" / "decision_memory_service.py",
        project_root / "app" / "decision_outcome_service.py",
        project_root / "frontend" / "src" / "pages" / "DecisionExplainabilityPage.tsx",
        project_root / "web" / "app.py",
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(
            "KAIRO Decision Explainability v0.6 and decision-memory "
            "foundations must be installed first. Missing: "
            + ", ".join(missing)
        )


def main() -> None:
    project_root = locate_project_root()
    validate_baseline(project_root)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = (
        project_root
        / "source-backups"
        / f"historical-similarity-v0.7-{timestamp}"
    )

    for relative in FILES:
        source = PAYLOAD_ROOT / relative
        destination = project_root / relative

        if not source.exists():
            raise RuntimeError(f"Bundle payload is missing: {relative}")

        if destination.exists():
            backup = backup_root / relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, backup)

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        print("Installed:", relative)

    print()
    print("Source backup:", backup_root)
    print("KAIRO Historical Similarity v0.7 installation complete.")


if __name__ == "__main__":
    main()
