from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

BUNDLE_ROOT = Path(__file__).resolve().parent
PAYLOAD_ROOT = BUNDLE_ROOT / "payload"
FILES = (
    "app/performance_review_service.py",
    "tests/test_performance_review_service.py",
    "frontend/src/lib/types.ts",
    "frontend/src/pages/PerformanceIntelligencePage.tsx",
    "frontend/src/__tests__/performance-intelligence.test.tsx",
)


def main() -> None:
    project_root = Path.cwd().resolve()
    required = (
        project_root / "app",
        project_root / "web",
        project_root / "frontend" / "src",
        project_root / "tests",
    )
    if not all(path.exists() for path in required):
        raise RuntimeError(
            "Run this installer from the trading-bot project root."
        )

    endpoint_source = project_root / "web" / "app.py"
    if (
        not endpoint_source.exists()
        or '"/api/performance/review"' not in endpoint_source.read_text(
            encoding="utf-8"
        )
    ):
        raise RuntimeError(
            "Performance Intelligence v1 backend is not installed. "
            "Install v1 before applying v2."
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = (
        project_root
        / "source-backups"
        / f"performance-intelligence-v2-{timestamp}"
    )

    for relative in FILES:
        source = PAYLOAD_ROOT / relative
        destination = project_root / relative
        if not source.exists():
            raise FileNotFoundError(f"Bundle payload is missing: {relative}")
        if destination.exists():
            backup = backup_root / relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, backup)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        print("Installed:", relative)

    print()
    print("Source backup:", backup_root)
    print("KAIRO Performance Intelligence v2 installation complete.")


if __name__ == "__main__":
    main()
