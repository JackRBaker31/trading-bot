import json
from datetime import datetime, timezone

import pytest

from app.supervisor_status_repository import SupervisorStatusRepository


def write_status(tmp_path, payload):
    path = tmp_path / "supervisor_status.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_loads_valid_supervisor_status(tmp_path) -> None:
    path = write_status(
        tmp_path,
        {
            "generated_at": "2026-07-22T10:00:00+00:00",
            "supervisor_status": "RUNNING",
            "supervisor_process_id": 123,
            "restart_enabled": True,
            "processes": [{"name": "api", "status": "RUNNING"}],
        },
    )
    repository = SupervisorStatusRepository(
        status_path=path,
        process_alive=lambda process_id: process_id == 123,
    )

    snapshot = repository.load()

    assert snapshot is not None
    assert snapshot.generated_at == datetime(
        2026, 7, 22, 10, 0, tzinfo=timezone.utc
    )
    assert snapshot.supervisor_status == "RUNNING"
    assert snapshot.supervisor_process_id == 123
    assert snapshot.restart_enabled is True
    assert snapshot.processes[0]["name"] == "api"
    assert repository.process_is_alive(123) is True


def test_returns_none_when_status_file_is_missing(tmp_path) -> None:
    repository = SupervisorStatusRepository(
        status_path=tmp_path / "missing.json"
    )

    assert repository.load() is None


def test_rejects_invalid_json(tmp_path) -> None:
    path = tmp_path / "supervisor_status.json"
    path.write_text("not-json", encoding="utf-8")
    repository = SupervisorStatusRepository(status_path=path)

    with pytest.raises(ValueError, match="could not be read"):
        repository.load()