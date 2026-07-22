from __future__ import annotations

import json
from pathlib import Path

from app.process_supervisor import ManagedProcessConfig, ProcessSupervisor


class FakeProcess:
    next_pid = 1000

    def __init__(self) -> None:
        self.pid = FakeProcess.next_pid
        FakeProcess.next_pid += 1
        self.exit_code = None
        self.terminated = False
        self.killed = False

    def poll(self):
        return self.exit_code

    def terminate(self) -> None:
        self.terminated = True
        self.exit_code = 0

    def wait(self, timeout=None):
        del timeout
        return 0 if self.exit_code is None else self.exit_code

    def kill(self) -> None:
        self.killed = True
        self.exit_code = -9


class FakePopenFactory:
    def __init__(self) -> None:
        self.processes: list[FakeProcess] = []
        self.calls: list[dict] = []

    def __call__(self, command, **kwargs):
        process = FakeProcess()
        self.processes.append(process)
        self.calls.append({"command": command, **kwargs})
        return process


def make_config(tmp_path: Path, *, health_probe=None):
    return ManagedProcessConfig(
        name="worker",
        command=("python", "-m", "example"),
        log_path=tmp_path / "worker.log",
        health_probe=health_probe,
        startup_grace_seconds=0,
    )


def test_starts_process_and_writes_status(tmp_path):
    factory = FakePopenFactory()
    supervisor = ProcessSupervisor(
        processes=[make_config(tmp_path)],
        working_directory=tmp_path,
        status_path=tmp_path / "status.json",
        pid_path=tmp_path / "supervisor.pid",
        popen_factory=factory,
        sleeper=lambda seconds: None,
    )

    supervisor.start_all()

    assert len(factory.processes) == 1
    assert supervisor.statuses()[0].status == "RUNNING"
    payload = json.loads((tmp_path / "status.json").read_text())
    assert payload["processes"][0]["name"] == "worker"
    supervisor.stop_all()


def test_restarts_process_after_unexpected_exit(tmp_path):
    factory = FakePopenFactory()
    supervisor = ProcessSupervisor(
        processes=[make_config(tmp_path)],
        working_directory=tmp_path,
        status_path=tmp_path / "status.json",
        pid_path=tmp_path / "supervisor.pid",
        popen_factory=factory,
        sleeper=lambda seconds: None,
    )
    supervisor.start_all()
    factory.processes[0].exit_code = 1

    supervisor.run_once()

    assert len(factory.processes) == 2
    status = supervisor.statuses()[0]
    assert status.status == "RUNNING"
    assert status.restart_count == 1
    supervisor.stop_all()


def test_restart_limit_prevents_crash_loop(tmp_path):
    factory = FakePopenFactory()
    now = [0.0]
    supervisor = ProcessSupervisor(
        processes=[make_config(tmp_path)],
        working_directory=tmp_path,
        status_path=tmp_path / "status.json",
        pid_path=tmp_path / "supervisor.pid",
        popen_factory=factory,
        sleeper=lambda seconds: None,
        clock=lambda: now[0],
        max_restarts=2,
    )
    supervisor.start_all()

    factory.processes[-1].exit_code = 1
    supervisor.run_once()
    factory.processes[-1].exit_code = 1
    supervisor.run_once()
    factory.processes[-1].exit_code = 1
    supervisor.run_once()

    assert len(factory.processes) == 3
    assert supervisor.statuses()[0].status == "FAILED"
    supervisor.stop_all()


def test_restarts_after_repeated_health_failures(tmp_path):
    factory = FakePopenFactory()
    supervisor = ProcessSupervisor(
        processes=[make_config(tmp_path, health_probe=lambda: False)],
        working_directory=tmp_path,
        status_path=tmp_path / "status.json",
        pid_path=tmp_path / "supervisor.pid",
        popen_factory=factory,
        sleeper=lambda seconds: None,
        health_failure_limit=2,
    )
    supervisor.start_all()

    supervisor.run_once()
    assert len(factory.processes) == 1
    supervisor.run_once()

    assert len(factory.processes) == 2
    assert supervisor.statuses()[0].restart_count == 1
    supervisor.stop_all()


def test_stop_all_terminates_children(tmp_path):
    factory = FakePopenFactory()
    supervisor = ProcessSupervisor(
        processes=[make_config(tmp_path)],
        working_directory=tmp_path,
        status_path=tmp_path / "status.json",
        pid_path=tmp_path / "supervisor.pid",
        popen_factory=factory,
        sleeper=lambda seconds: None,
    )
    supervisor.start_all()

    supervisor.stop_all()

    assert factory.processes[0].terminated is True
    payload = json.loads((tmp_path / "status.json").read_text())
    assert payload["supervisor_status"] == "STOPPED"