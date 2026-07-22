from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.supervisor_diagnostics import build_diagnostics


def test_diagnostics_reads_status_database_and_logs(tmp_path: Path, monkeypatch):
    database = tmp_path / "application.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE example (id INTEGER)")

    log_path = tmp_path / "api.log"
    log_path.write_text("started\nhealthy\n", encoding="utf-8")
    status_path = tmp_path / "status.json"
    status_path.write_text(json.dumps({
        "supervisor_status": "RUNNING",
        "processes": [{
            "name": "api", "status": "RUNNING", "process_id": 10,
            "restart_state": "HEALTHY", "restart_count": 0,
            "last_restart_reason": None, "health": {"healthy": True},
            "log_path": str(log_path),
        }],
    }), encoding="utf-8")

    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: Response())
    result = build_diagnostics(status_path=status_path, database_path=database, recent_log_lines=1)

    assert result["database"]["accessible"] is True
    assert result["api_readiness"]["reachable"] is True
    assert result["processes"][0]["log"]["recent_lines"] == ["healthy"]


def test_diagnostics_handles_missing_files(tmp_path: Path, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("offline")
    monkeypatch.setattr("urllib.request.urlopen", fail)
    result = build_diagnostics(status_path=tmp_path / "missing.json", database_path=tmp_path / "missing.db")
    assert result["supervisor"]["status_file_exists"] is False
    assert result["database"]["accessible"] is False
    assert result["api_readiness"]["reachable"] is False