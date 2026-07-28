from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


BUNDLE_ROOT = Path(__file__).resolve().parent
PAYLOAD_ROOT = BUNDLE_ROOT / "payload"

FILES = (
    "app/opportunity_ranking_models.py",
    "app/opportunity_ranking_service.py",
    "web/dependencies.py",
    "web/app.py",
    "frontend/src/hooks/useOpportunityRanking.ts",
    "frontend/src/pages/OpportunityRankingPage.tsx",
    "frontend/src/App.tsx",
    "frontend/src/components/AppShell.tsx",
    "tests/test_opportunity_ranking_service.py",
    "tests/test_web_opportunity_ranking.py",
    "frontend/src/__tests__/opportunity-ranking.test.tsx",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install KAIRO Opportunity Ranking v0.9."
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        help="Trading-bot project root. Defaults to the current folder.",
    )
    return parser.parse_args()


def locate_project_root(value: str | None) -> Path:
    current = Path(value).expanduser().resolve() if value else Path.cwd().resolve()

    if (
        (current / "app").is_dir()
        and (current / "frontend" / "src").is_dir()
        and (current / "web").is_dir()
        and (current / "tests").is_dir()
        and (current / "run_kairo.py").is_file()
    ):
        return current

    if (
        current.name.lower() == "frontend"
        and (current / "src").is_dir()
        and (current.parent / "app").is_dir()
        and (current.parent / "run_kairo.py").is_file()
    ):
        return current.parent

    raise RuntimeError(
        "Project root was not found. Pass the full trading-bot path, for example: "
        r"C:\Users\Jack\Documents\trading-bot"
    )


def validate_baseline(project_root: Path) -> None:
    required = (
        project_root / "app" / "market_data_resilience.py",
        project_root / "app" / "historical_similarity_service.py",
        project_root / "app" / "investment_thesis_service.py",
        project_root / "app" / "performance_review_service.py",
        project_root / "frontend" / "src" / "pages" / "DecisionExplainabilityPage.tsx",
        project_root / "frontend" / "src" / "pages" / "OperationsPage.tsx",
        project_root / "run_kairo.py",
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(
            "KAIRO v0.8.1 must be installed first. Missing: "
            + ", ".join(missing)
        )


def pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            check=False,
            capture_output=True,
            text=True,
        )
        output = result.stdout.strip()
        return bool(output) and "No tasks are running" not in output
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def ensure_supervisor_stopped(project_root: Path) -> None:
    lock_path = project_root / "data" / "runtime" / "kairo-monitor.json"
    if not lock_path.exists():
        return
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        payload = {}
    pid = payload.get("pid") if isinstance(payload, dict) else None
    if isinstance(pid, int) and pid_is_running(pid):
        raise RuntimeError(
            "KAIRO Platform Supervisor is still running. Press Ctrl+C in its "
            "window, then run Stop Everything.bat before installing."
        )
    lock_path.unlink(missing_ok=True)


def main() -> None:
    args = parse_args()
    project_root = locate_project_root(args.project_root)
    validate_baseline(project_root)
    ensure_supervisor_stopped(project_root)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = (
        project_root
        / "source-backups"
        / f"opportunity-ranking-v0.9-{timestamp}"
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
    print("KAIRO Opportunity Ranking v0.9 installation complete.")
    print("Start KAIRO using Start Everything.bat.")


if __name__ == "__main__":
    main()
