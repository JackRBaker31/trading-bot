from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path


BUNDLE_ROOT = Path(__file__).resolve().parent
PAYLOAD_ROOT = BUNDLE_ROOT / "payload"

FILES = (
    "app/market_data.py",
    "app/twelve_data_historical_data.py",
    "app/market_data_resilience.py",
    "app/infrastructure_status_service.py",
    "web/dependencies.py",
    "web/app.py",
    "frontend/src/lib/types.ts",
    "frontend/src/pages/OperationsPage.tsx",
    "frontend/src/hooks/useTechnicalAnalysis.ts",
    "frontend/src/hooks/useMacroAnalysis.ts",
    "frontend/src/hooks/useAdvancedIntelligence.ts",
    "frontend/src/components/copilot/TechnicalAnalysisPanel.tsx",
    "frontend/src/components/copilot/MacroAnalysisPanel.tsx",
    "frontend/src/components/copilot/AdvancedIntelligencePanel.tsx",
    "frontend/src/__tests__/operations-centre.test.tsx",
    "tests/test_market_data_resilience.py",
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
        project_root / "app" / "twelve_data_historical_data.py",
        project_root / "app" / "historical_similarity_service.py",
        project_root / "frontend" / "src" / "pages" / "OperationsPage.tsx",
        project_root / "frontend" / "src" / "pages" / "DecisionExplainabilityPage.tsx",
        project_root / "web" / "app.py",
        project_root / "web" / "dependencies.py",
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(
            "KAIRO Historical Similarity v0.7 and the current Operations "
            "Centre must be installed first. Missing: "
            + ", ".join(missing)
        )


def main() -> None:
    project_root = locate_project_root()
    validate_baseline(project_root)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = (
        project_root
        / "source-backups"
        / f"market-data-resilience-v0.8-{timestamp}"
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

    cache_directory = project_root / "data" / "runtime" / "market-data-cache"
    cache_directory.mkdir(parents=True, exist_ok=True)

    print()
    print("Source backup:", backup_root)
    print("Market-data cache:", cache_directory)
    print("KAIRO Market Data Resilience v0.8 installation complete.")


if __name__ == "__main__":
    main()
