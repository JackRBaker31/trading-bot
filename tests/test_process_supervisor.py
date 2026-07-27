from __future__ import annotations

import json
from pathlib import Path

from app.health_monitor import ServiceHealth
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

    def __call__(self, command, **kwargs):
        del command, kwargs
        process = FakeProcess()
        self.processes.append(process)
        return process


class FakeHealthMonitor:
    def __init__(self, result: ServiceHealth, *, name: str = "worker") -> None:
        self.result = result
        self.name = name
        self.calls = 0

    def check_all(self):
        self.calls += 1
        return {self.name: self.result}


def make_config(tmp_path: Path, *, name: str = "worker"):
    return ManagedProcessConfig(
        name=name,
        command=("python", "-m", "example"),
        log_path=tmp_path / f"{name}.log",
    )


def make_health(
    *,
    name: str = "worker",
    healthy: bool,
    persistent_fault: bool,
    heartbeat_process_id: int | None = None,
) -> ServiceHealth:
    return ServiceHealth(
        name=name,
        health_status="HEALTHY" if healthy else "STALE",
        healthy=healthy,
        persistent_fault=persistent_fault,
        consecutive_health_failures=3 if persistent_fault else 0,
        last_health_check_at="2026-07-22T12:00:00+00:00",
        last_healthy_at=None,
        health_detail="test result",
        heartbeat_process_id=heartbeat_process_id,
    )


def make_supervisor(
    tmp_path: Path,
    *,
    config: ManagedProcessConfig | None = None,
    factory: FakePopenFactory | None = None,
    health_monitor=None,
    clock=lambda: 100.0,
    max_restarts: int = 5,
    recovery_grace_seconds: float = 0.0,
):
    actual_factory = factory or FakePopenFactory()
    return ProcessSupervisor(
        processes=[config or make_config(tmp_path)],
        working_directory=tmp_path,
        status_path=tmp_path / "status.json",
        pid_path=tmp_path / "supervisor.pid",
        popen_factory=actual_factory,
        sleeper=lambda seconds: None,
        clock=clock,
        max_restarts=max_restarts,
        recovery_grace_seconds=recovery_grace_seconds,
        health_monitor=health_monitor,
    )


def test_starts_process_and_writes_status(tmp_path):
    factory = FakePopenFactory()
    supervisor = make_supervisor(tmp_path, factory=factory)

    supervisor.start_all()

    assert len(factory.processes) == 1
    assert supervisor.statuses()[0].status == "RUNNING"
    payload = json.loads((tmp_path / "status.json").read_text())
    assert payload["processes"][0]["name"] == "worker"
    supervisor.stop_all()


def test_restarts_process_after_unexpected_exit(tmp_path):
    factory = FakePopenFactory()
    supervisor = make_supervisor(tmp_path, factory=factory)
    supervisor.start_all()
    factory.processes[0].exit_code = 1

    supervisor.run_once()

    assert len(factory.processes) == 2
    status = supervisor.statuses()[0]
    assert status.restart_count == 1
    assert status.restart_state == "RECOVERING"
    supervisor.stop_all()


def test_persistent_api_fault_restarts_owned_api(tmp_path):
    factory = FakePopenFactory()
    health_monitor = FakeHealthMonitor(
        make_health(name="api", healthy=False, persistent_fault=True),
        name="api",
    )
    supervisor = make_supervisor(
        tmp_path,
        config=make_config(tmp_path, name="api"),
        factory=factory,
        health_monitor=health_monitor,
    )
    supervisor.start_all()

    supervisor.run_once()

    assert factory.processes[0].terminated is True
    assert len(factory.processes) == 2
    status = supervisor.statuses()[0]
    assert status.restart_count == 1
    assert status.restart_state == "RECOVERING"
    assert "persistent health fault" in status.last_restart_reason
    supervisor.stop_all()


def test_persistent_worker_fault_requires_matching_heartbeat_pid(tmp_path):
    factory = FakePopenFactory()
    supervisor = make_supervisor(tmp_path, factory=factory)
    supervisor.start_all()
    owned_pid = factory.processes[0].pid
    supervisor._health_monitor = FakeHealthMonitor(
        make_health(
            healthy=False,
            persistent_fault=True,
            heartbeat_process_id=owned_pid,
        )
    )

    supervisor.run_once()

    assert factory.processes[0].terminated is True
    assert len(factory.processes) == 2
    supervisor.stop_all()


def test_pid_mismatch_reports_fault_without_restart(tmp_path):
    factory = FakePopenFactory()
    health_monitor = FakeHealthMonitor(
        make_health(
            healthy=False,
            persistent_fault=True,
            heartbeat_process_id=999999,
        )
    )
    supervisor = make_supervisor(
        tmp_path,
        factory=factory,
        health_monitor=health_monitor,
    )
    supervisor.start_all()

    supervisor.run_once()

    assert len(factory.processes) == 1
    assert factory.processes[0].terminated is False
    assert supervisor.statuses()[0].restart_state == "FAULT_DETECTED"
    supervisor.stop_all()


def test_non_persistent_health_fault_does_not_restart(tmp_path):
    factory = FakePopenFactory()
    health_monitor = FakeHealthMonitor(
        make_health(healthy=False, persistent_fault=False)
    )
    supervisor = make_supervisor(
        tmp_path,
        factory=factory,
        health_monitor=health_monitor,
    )
    supervisor.start_all()

    supervisor.run_once()

    assert len(factory.processes) == 1
    assert supervisor.statuses()[0].restart_state == "FAULT_DETECTED"
    supervisor.stop_all()


def test_recovery_grace_prevents_immediate_health_restart(tmp_path):
    factory = FakePopenFactory()
    clock = [100.0]
    health_monitor = FakeHealthMonitor(
        make_health(name="api", healthy=False, persistent_fault=True),
        name="api",
    )
    supervisor = make_supervisor(
        tmp_path,
        config=make_config(tmp_path, name="api"),
        factory=factory,
        health_monitor=health_monitor,
        clock=lambda: clock[0],
        recovery_grace_seconds=15.0,
    )
    supervisor.start_all()

    clock[0] = 110.0
    supervisor.run_once()

    assert len(factory.processes) == 1
    supervisor.stop_all()


def test_healthy_check_marks_recovery_complete(tmp_path):
    factory = FakePopenFactory()
    health_monitor = FakeHealthMonitor(
        make_health(name="api", healthy=False, persistent_fault=True),
        name="api",
    )
    supervisor = make_supervisor(
        tmp_path,
        config=make_config(tmp_path, name="api"),
        factory=factory,
        health_monitor=health_monitor,
    )
    supervisor.start_all()
    supervisor.run_once()
    health_monitor.result = make_health(
        name="api", healthy=True, persistent_fault=False
    )

    supervisor.run_once()

    assert supervisor.statuses()[0].restart_state == "RECOVERED"
    assert supervisor.statuses()[0].recovered_at is not None
    supervisor.stop_all()


def test_restart_limit_prevents_crash_loop(tmp_path):
    factory = FakePopenFactory()
    now = [0.0]
    supervisor = make_supervisor(
        tmp_path,
        factory=factory,
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
    assert supervisor.statuses()[0].restart_state == "FAILED"
    supervisor.stop_all()


def test_stop_all_terminates_children(tmp_path):
    factory = FakePopenFactory()
    supervisor = make_supervisor(tmp_path, factory=factory)
    supervisor.start_all()

    supervisor.stop_all()

    assert factory.processes[0].terminated is True
    payload = json.loads((tmp_path / "status.json").read_text())
    assert payload["supervisor_status"] == "STOPPED"

class FakeAlertTransport:
    def __init__(self) -> None:
        self.requests: list[dict[str, object]] = []

    def post(
        self,
        *,
        url: str,
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> None:
        self.requests.append(
            {
                "url": url,
                "payload": payload,
                "timeout_seconds": timeout_seconds,
            }
        )


def make_alerting_hook(transport: FakeAlertTransport):
    from app.supervisor_alerting import SupervisorAlertingHook

    return SupervisorAlertingHook(
        webhook_url="https://alerts.example.test/kairo",
        transport=transport,
    )


def test_alerts_when_process_crashes(tmp_path) -> None:
    factory = FakePopenFactory()
    transport = FakeAlertTransport()
    supervisor = ProcessSupervisor(
        processes=[make_config(tmp_path)],
        working_directory=tmp_path,
        status_path=tmp_path / "status.json",
        pid_path=tmp_path / "supervisor.pid",
        popen_factory=factory,
        sleeper=lambda seconds: None,
        alerting_hook=make_alerting_hook(transport),
    )
    supervisor.start_all()
    factory.processes[0].exit_code = 1

    supervisor.run_once()

    events = [
        request["payload"]["event_type"]
        for request in transport.requests
    ]
    assert "process_crash" in events
    supervisor.stop_all()


def test_alerts_after_repeated_restart_failures(tmp_path) -> None:
    factory = FakePopenFactory()
    transport = FakeAlertTransport()
    supervisor = ProcessSupervisor(
        processes=[make_config(tmp_path)],
        working_directory=tmp_path,
        status_path=tmp_path / "status.json",
        pid_path=tmp_path / "supervisor.pid",
        popen_factory=factory,
        sleeper=lambda seconds: None,
        alerting_hook=make_alerting_hook(transport),
    )
    supervisor.start_all()

    factory.processes[-1].exit_code = 1
    supervisor.run_once()
    factory.processes[-1].exit_code = 1
    supervisor.run_once()

    events = [
        request["payload"]["event_type"]
        for request in transport.requests
    ]
    assert "repeated_restart_failure" in events
    supervisor.stop_all()


def test_alerts_when_supervisor_gives_up(tmp_path) -> None:
    factory = FakePopenFactory()
    transport = FakeAlertTransport()
    supervisor = ProcessSupervisor(
        processes=[make_config(tmp_path)],
        working_directory=tmp_path,
        status_path=tmp_path / "status.json",
        pid_path=tmp_path / "supervisor.pid",
        popen_factory=factory,
        sleeper=lambda seconds: None,
        max_restarts=1,
        alerting_hook=make_alerting_hook(transport),
    )
    supervisor.start_all()

    factory.processes[-1].exit_code = 1
    supervisor.run_once()
    factory.processes[-1].exit_code = 1
    supervisor.run_once()

    events = [
        request["payload"]["event_type"]
        for request in transport.requests
    ]
    assert "supervisor_gave_up" in events
    supervisor.stop_all()
