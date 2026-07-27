from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

BUNDLE_ROOT = Path(__file__).resolve().parent
PAYLOAD_ROOT = BUNDLE_ROOT / "payload"
FILES = (
    "src/App.tsx",
    "src/components/AppShell.tsx",
    "src/hooks/usePerformanceReview.ts",
    "src/lib/types.ts",
    "src/pages/PerformanceIntelligencePage.tsx",
    "src/__tests__/performance-intelligence.test.tsx",
)


def main() -> None:
    frontend_root = Path.cwd().resolve()

    if not (
        (frontend_root / "package.json").is_file()
        and (frontend_root / "src").is_dir()
    ):
        raise RuntimeError(
            "Run this installer from the frontend folder."
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = (
        frontend_root
        / "source-backups"
        / f"performance-frontend-{timestamp}"
    )

    for relative in FILES:
        source = PAYLOAD_ROOT / relative
        destination = frontend_root / relative

        if destination.exists():
            backup = backup_root / relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, backup)

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        print("Installed:", relative)

    print()
    print("Source backup:", backup_root)
    print("Performance Intelligence frontend installation complete.")


if __name__ == "__main__":
    main()
