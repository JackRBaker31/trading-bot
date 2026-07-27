from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

BUNDLE_ROOT = Path(__file__).resolve().parent
PAYLOAD_ROOT = BUNDLE_ROOT / "payload"
FILES = (
    "app/performance_review_service.py",
    "web/dependencies.py",
    "web/app.py",
    "frontend/src/lib/types.ts",
    "frontend/src/hooks/usePerformanceReview.ts",
    "frontend/src/pages/PerformanceIntelligencePage.tsx",
    "frontend/src/App.tsx",
    "frontend/src/components/AppShell.tsx",
    "frontend/src/__tests__/performance-intelligence.test.tsx",
    "tests/test_performance_review_service.py",
)


def main() -> None:
    project_root = Path.cwd().resolve()
    if not all((project_root / name).is_dir() for name in ("app", "web", "frontend", "tests")):
        raise RuntimeError("Run this installer from the trading-bot project root.")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = project_root / "source-backups" / f"performance-intelligence-v1-{timestamp}"

    for relative in FILES:
        source = PAYLOAD_ROOT / relative
        destination = project_root / relative
        if destination.exists():
            backup = backup_root / relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, backup)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        print("Installed:", relative)

    print()
    print("Source backup:", backup_root)
    print("KAIRO Performance Intelligence v1 installation complete.")


if __name__ == "__main__":
    main()
