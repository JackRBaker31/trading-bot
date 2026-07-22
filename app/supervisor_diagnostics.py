from __future__ import annotations

import json
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.supervisor_logging import tail_lines


def build_diagnostics(
    *,
    status_path: str | Path = "data/supervisor_status.json",
    database_path: str | Path = "data/application.db",
    api_ready_url: str = "http://127.0.0.1:8000/health/ready",
    recent_log_lines: int = 10,
) -> dict[str, Any]:
    status_file = Path(status_path)
    status: dict[str, Any] | None = None
    status_error: str | None = None
    if status_file.exists():
        try:
            status = json.loads(status_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            status_error = f"{type(error).__name__}: {error}"
    else:
        status_error = "Supervisor status file does not exist."

    database = _check_database(Path(database_path))
    api = _check_api(api_ready_url)
    processes = []
    for process in (status or {}).get("processes", []):
        log_path = process.get("log_path")
        log_file = Path(log_path) if isinstance(log_path, str) else None
        processes.append({
            "name": process.get("name"),
            "status": process.get("status"),
            "process_id": process.get("process_id"),
            "restart_state": process.get("restart_state"),
            "restart_count": process.get("restart_count"),
            "last_restart_reason": process.get("last_restart_reason"),
            "health": process.get("health"),
            "log": {
                "path": str(log_file) if log_file else None,
                "exists": bool(log_file and log_file.exists()),
                "size_bytes": log_file.stat().st_size if log_file and log_file.exists() else 0,
                "recent_lines": tail_lines(log_file, recent_log_lines) if log_file else [],
            },
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "supervisor": {
            "status_file": str(status_file),
            "status_file_exists": status_file.exists(),
            "status_error": status_error,
            "status": status,
        },
        "api_readiness": api,
        "database": database,
        "processes": processes,
    }


def _check_database(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "accessible": False, "detail": "Database file does not exist."}
    try:
        with sqlite3.connect(path) as connection:
            connection.execute("SELECT 1").fetchone()
        return {"path": str(path), "accessible": True, "detail": "SQLite database is readable."}
    except sqlite3.Error as error:
        return {"path": str(path), "accessible": False, "detail": f"{type(error).__name__}: {error}"}


def _check_api(url: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=2.0) as response:
            return {"url": url, "reachable": 200 <= response.status < 300, "status_code": response.status}
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return {"url": url, "reachable": False, "status_code": None, "detail": f"{type(error).__name__}: {error}"}