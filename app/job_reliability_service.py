from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class JobReliabilityService:
    def __init__(
        self,
        *,
        database_path: str = "data/application.db",
        crash_directory: str = "data/runtime/crashes",
        launcher_events_path: str = "data/runtime/launcher-events.jsonl",
    ) -> None:
        self._database_path = Path(database_path)
        self._crash_directory = Path(crash_directory)
        self._launcher_events_path = Path(launcher_events_path)

    def get_status(self) -> dict[str, object]:
        now = datetime.now(timezone.utc)
        counts = self._job_counts()
        crashes = self._crash_reports()
        restarts = self._restart_events()
        latest_crash = crashes[-1] if crashes else None
        return {
            "generated_at": now.isoformat(),
            "job_counts": counts,
            "abandoned_running_jobs": counts.get("RUNNING", 0),
            "crash_report_count": len(crashes),
            "worker_restart_count": len(restarts),
            "latest_crash": latest_crash,
            "latest_restart": restarts[-1] if restarts else None,
        }

    def _job_counts(self) -> dict[str, int]:
        if not self._database_path.exists():
            return {}
        with sqlite3.connect(self._database_path) as connection:
            rows = connection.execute(
                "SELECT status, COUNT(*) FROM jobs GROUP BY status"
            ).fetchall()
        return {str(status): int(count) for status, count in rows}

    def _crash_reports(self) -> list[dict[str, object]]:
        if not self._crash_directory.exists():
            return []
        reports = []
        for path in sorted(self._crash_directory.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            reports.append({
                "timestamp": payload.get("timestamp"),
                "job_id": payload.get("job_id"),
                "job_type": payload.get("job_type"),
                "stage": payload.get("stage"),
                "exception_type": payload.get("exception_type"),
                "report_path": str(path),
            })
        return reports

    def _restart_events(self) -> list[dict[str, object]]:
        if not self._launcher_events_path.exists():
            return []
        events = []
        for line in self._launcher_events_path.read_text(
            encoding="utf-8"
        ).splitlines():
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if payload.get("event") == "SERVICE_RESTARTED":
                events.append(payload)
        return events
