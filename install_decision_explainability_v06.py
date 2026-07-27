from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

BUNDLE_ROOT = Path(__file__).resolve().parent
PAYLOAD_ROOT = BUNDLE_ROOT / "payload" / "frontend"

FILES = (
    "src/App.tsx",
    "src/components/AppShell.tsx",
    "src/pages/CopilotPage.tsx",
    "src/pages/ShadowIntelligencePage.tsx",
    "src/pages/DecisionExplainabilityPage.tsx",
    "src/__tests__/decision-explainability.test.tsx",
)


def locate_project_root() -> Path:
    current = Path.cwd().resolve()

    if (
        (current / "app").is_dir()
        and (current / "frontend" / "src").is_dir()
        and (current / "web").is_dir()
    ):
        return current

    if (
        current.name.lower() == "frontend"
        and (current / "src").is_dir()
        and (current.parent / "app").is_dir()
    ):
        return current.parent

    raise RuntimeError(
        "Run this installer from the trading-bot project root "
        "or its frontend folder."
    )


def main() -> None:
    project_root = locate_project_root()
    frontend_root = project_root / "frontend"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = (
        project_root
        / "source-backups"
        / f"decision-explainability-v0.6-{timestamp}"
        / "frontend"
    )

    for relative in FILES:
        source = PAYLOAD_ROOT / relative
        destination = frontend_root / relative

        if not source.exists():
            raise RuntimeError(f"Bundle payload is missing: {relative}")

        if destination.exists():
            backup = backup_root / relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, backup)

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        print("Installed:", f"frontend/{relative}")

    print()
    print("Source backup:", backup_root)
    print("KAIRO Decision Explainability v0.6 installation complete.")


if __name__ == "__main__":
    main()
