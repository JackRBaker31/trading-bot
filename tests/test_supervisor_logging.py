from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.supervisor_logging import LogRotationConfig, SupervisorEventLogger, rotate_file, tail_lines


def test_rotation_config_validates_values():
    with pytest.raises(ValueError):
        LogRotationConfig(max_bytes=0)
    with pytest.raises(ValueError):
        LogRotationConfig(backup_count=-1)


def test_rotate_file_keeps_numbered_backups(tmp_path: Path):
    path = tmp_path / "api.log"
    path.write_text("first", encoding="utf-8")
    config = LogRotationConfig(max_bytes=1, backup_count=2)

    assert rotate_file(path, config) is True
    path.write_text("second", encoding="utf-8")
    assert rotate_file(path, config) is True

    assert (tmp_path / "api.log.1").read_text() == "second"
    assert (tmp_path / "api.log.2").read_text() == "first"


def test_event_logger_writes_structured_json(tmp_path: Path):
    path = tmp_path / "supervisor.log"
    logger = SupervisorEventLogger(path, rotation=LogRotationConfig(max_bytes=1000, backup_count=1))

    logger.log("process_started", name="api", process_id=123)

    payload = json.loads(path.read_text().strip())
    assert payload["event_type"] == "process_started"
    assert payload["name"] == "api"
    assert payload["process_id"] == 123
    assert payload["timestamp"]


def test_tail_lines_returns_recent_content(tmp_path: Path):
    path = tmp_path / "worker.log"
    path.write_text("one\ntwo\nthree\n", encoding="utf-8")
    assert tail_lines(path, 2) == ["two", "three"]