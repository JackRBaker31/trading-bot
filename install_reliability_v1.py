from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

BUNDLE_ROOT = Path(__file__).resolve().parent
PAYLOAD_ROOT = BUNDLE_ROOT / "payload"
FILES = (
    "app/job_crash_reporting.py",
    "app/job_recovery_service.py",
    "app/job_reliability_service.py",
    "app/job_repository.py",
    "app/job_service.py",
    "app/job_worker.py",
    "app/job_executor.py",
    "app/intelligence_cycle_service.py",
    "app/run_job_worker.py",
    "web/app.py",
    "run_reliability_repair.py",
    "tests/test_job_reliability.py",
    "tests/test_job_reliability_service.py",
)


def main() -> None:
    project = Path.cwd().resolve()
    if not ((project / "app").is_dir() and (project / "web").is_dir()):
        raise RuntimeError(
            "Run this installer from the trading-bot project root."
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = (
        project / "source-backups" / f"reliability-v1-{timestamp}"
    )

    for relative in FILES:
        existing = project / relative
        if existing.exists():
            backup = backup_root / relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(existing, backup)

        source = PAYLOAD_ROOT / relative
        destination = project / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        print("Installed:", relative)

    print()
    print("Source backup:", backup_root)
    print("KAIRO Reliability v1 installation complete.")


if __name__ == "__main__":
    main()
