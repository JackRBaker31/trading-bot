from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Protocol, TextIO

from app.health_monitor import HealthMonitor, ServiceHealth
from app.restart_policy import RestartPolicy, RestartPolicyConfig


class SpawnedProcess(Protocol):
    pid: int

    def poll(self) -> int | None: ...

    def terminate(self) -> None: ...

    def wait(self, timeout: float | None = None) -> int: ...

    def kill(self) -> None: ...


PopenFactory = Callable[..., SpawnedProcess]
Clock = Callable[[], float]
Sleeper = Callable[[float], None]


@dataclass(frozen=True)
class ManagedProcessConfig:
    name: str
    command: tuple[str, ...]
    log_path: Path

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Managed process name is required.")
        if not self.command:
            raise ValueError("Managed process command is required.")


@dataclass
class ManagedProcessState:
    config: ManagedProcessConfig
    process: SpawnedProcess | None = None
    log_handle: TextIO | None = None
    started_monotonic: float | None = None
    started_at: datetime | None = None
    last_exit_code: int | None = None
    restart_count: int = 0
    restart_times: deque[float] = field(default_factory=deque)
    restart_state: str = "HEALTHY"
    last_restart_reason: str | None = None
    last_restart_at: datetime | None = None
    recovered_at: datetime | None = None


@dataclass(frozen=True)
class ProcessStatus:
    name: str
    status: str
    process_id: int | None
    restart_count: int
    restart_state: str
    last_restart_reason: str | None
    last_restart_at: str | None
    recovered_at: str | None
    last_exit_code: int | None
    health: dict[str, object] | None
    started_at: str | None
    log_path: str

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "process_id": self.process_id,
            "restart_count": self.restart_count,
            "restart_state": self.restart_state,
            "last_restart_reason": self.last_restart_reason,
            "last_restart_at": self.last_restart_at,
            "recovered_at": self.recovered_at,
            "last_exit_code": self.last_exit_code,
            "health": self.health,
            "started_at": self.started_at,
            "log_path": self.log_path,
        }


class ProcessSupervisor:
    def __init__(
        self,
        *,
        processes: list[ManagedProcessConfig],
        working_directory: str | Path = ".",
        status_path: str | Path = "data/supervisor_status.json",
        pid_path: str | Path = "data/kairo_supervisor.pid",
        check_seconds: float = 2.0,
        restart_enabled: bool = True,
        max_restarts: int = 5,
        restart_window_seconds: float = 300.0,
        recovery_grace_seconds: float = 15.0,
        health_monitor: HealthMonitor | None = None,
        restart_policy: RestartPolicy | None = None,
        popen_factory: PopenFactory = subprocess.Popen,
        clock: Clock = time.monotonic,
        sleeper: Sleeper = time.sleep,
    ) -> None:
        if not processes:
            raise ValueError("At least one managed process is required.")
        if check_seconds <= 0:
            raise ValueError("Check interval must be positive.")
        names = [item.name for item in processes]
        if len(names) != len(set(names)):
            raise ValueError("Managed process names must be unique.")

        self._working_directory = Path(working_directory).resolve()
        self._status_path = Path(status_path)
        self._pid_path = Path(pid_path)
        self._check_seconds = check_seconds
        self._restart_enabled = restart_enabled
        self._health_monitor = health_monitor
        self._health_results: dict[str, ServiceHealth] = {}
        self._restart_policy = restart_policy or RestartPolicy(
            RestartPolicyConfig(
                max_restarts=max_restarts,
                restart_window_seconds=restart_window_seconds,
                recovery_grace_seconds=recovery_grace_seconds,
            )
        )
        self._popen_factory = popen_factory
        self._clock = clock
        self._sleeper = sleeper
        self._states = {
            config.name: ManagedProcessState(config=config)
            for config in processes
        }
        self._stopping = False

    def acquire(self) -> None:
        self._pid_path.parent.mkdir(parents=True, exist_ok=True)
        if self._pid_path.exists():
            existing_pid = self._read_pid()
            if existing_pid is not None and self._process_alive(existing_pid):
                raise RuntimeError(
                    f"KAIRO supervisor is already running with PID {existing_pid}."
                )
            self._pid_path.unlink(missing_ok=True)

        descriptor = os.open(
            self._pid_path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
        )
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            file.write(str(os.getpid()))

    def release(self) -> None:
        self._pid_path.unlink(missing_ok=True)

    def start_all(self) -> None:
        for state in self._states.values():
            self._start(state, recovering=False)
        self.write_status()

    def run_once(self) -> None:
        for state in self._states.values():
            self._check_process(state)

        if self._health_monitor is not None:
            self._health_results = self._health_monitor.check_all()
            for state in self._states.values():
                health = self._health_results.get(state.config.name)
                if health is not None:
                    self._apply_health_result(state, health)

        self.write_status()

    def run_forever(self) -> None:
        self.acquire()
        try:
            self.start_all()
            while not self._stopping:
                self.run_once()
                self._sleeper(self._check_seconds)
        finally:
            self.stop_all()
            self.release()

    def request_stop(self) -> None:
        self._stopping = True

    def stop_all(self, *, terminate_timeout: float = 10.0) -> None:
        self._stopping = True
        for state in reversed(list(self._states.values())):
            self._stop(state, terminate_timeout=terminate_timeout)
        self.write_status(supervisor_status="STOPPED")

    def statuses(self) -> list[ProcessStatus]:
        return [self._status_for(state) for state in self._states.values()]

    def write_status(self, *, supervisor_status: str = "RUNNING") -> None:
        self._status_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "supervisor_status": supervisor_status,
            "supervisor_process_id": os.getpid(),
            "restart_enabled": self._restart_enabled,
            "processes": [status.to_dict() for status in self.statuses()],
        }
        temporary = self._status_path.with_suffix(
            self._status_path.suffix + ".tmp"
        )
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(self._status_path)

    def _start(self, state: ManagedProcessState, *, recovering: bool) -> None:
        state.config.log_path.parent.mkdir(parents=True, exist_ok=True)
        state.log_handle = state.config.log_path.open(
            "a", encoding="utf-8", buffering=1
        )
        self._write_log_banner(state, "STARTING")

        creation_flags = 0
        start_new_session = False
        if os.name == "nt":
            creation_flags = getattr(
                subprocess, "CREATE_NEW_PROCESS_GROUP", 0
            )
        else:
            start_new_session = True

        state.process = self._popen_factory(
            list(state.config.command),
            cwd=str(self._working_directory),
            stdout=state.log_handle,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=creation_flags,
            start_new_session=start_new_session,
        )
        state.started_monotonic = self._clock()
        state.started_at = datetime.now(timezone.utc)
        state.last_exit_code = None
        state.restart_state = "RECOVERING" if recovering else "HEALTHY"

    def _check_process(self, state: ManagedProcessState) -> None:
        process = state.process
        if process is None:
            self._restart(state, reason="process is not running")
            return

        exit_code = process.poll()
        if exit_code is None:
            return

        state.last_exit_code = int(exit_code)
        self._close_log(state)
        state.process = None
        self._restart(state, reason=f"process exited with code {exit_code}")

    def _apply_health_result(
        self,
        state: ManagedProcessState,
        health: ServiceHealth,
    ) -> None:
        process = state.process
        if process is None or process.poll() is not None:
            return

        now = self._clock()
        in_recovery_grace = self._restart_policy.within_recovery_grace(
            started_monotonic=state.started_monotonic,
            now=now,
        )

        if health.healthy:
            if state.restart_state == "RECOVERING":
                state.restart_state = "RECOVERED"
                state.recovered_at = datetime.now(timezone.utc)
                self._write_log_banner(state, "RECOVERED")
            elif state.restart_state not in {"RECOVERED", "FAILED"}:
                state.restart_state = "HEALTHY"
            return

        if in_recovery_grace or health.health_status == "STARTING":
            return

        if not health.persistent_fault:
            state.restart_state = "FAULT_DETECTED"
            return

        if not self._health_pid_matches_owned_process(state, health):
            state.restart_state = "FAULT_DETECTED"
            self._write_log_banner(
                state,
                "HEALTH FAULT NOT RESTARTED - HEARTBEAT PID DOES NOT MATCH OWNED PROCESS",
            )
            return

        self._restart(
            state,
            reason=(
                f"persistent health fault: {health.health_status} - "
                f"{health.health_detail}"
            ),
            terminate_running=True,
        )

    @staticmethod
    def _health_pid_matches_owned_process(
        state: ManagedProcessState,
        health: ServiceHealth,
    ) -> bool:
        process = state.process
        if process is None:
            return False
        if state.config.name == "api":
            return True
        return health.heartbeat_process_id == process.pid

    def _restart(
        self,
        state: ManagedProcessState,
        *,
        reason: str,
        terminate_running: bool = False,
    ) -> None:
        if self._stopping or not self._restart_enabled:
            return

        now = self._clock()
        decision = self._restart_policy.decide(
            restart_times=state.restart_times,
            now=now,
            reason=reason,
        )
        state.last_restart_reason = reason

        if not decision.allowed:
            state.restart_state = "FAILED"
            self._write_log_banner(
                state,
                "RESTART LIMIT REACHED - MANUAL REVIEW REQUIRED",
            )
            return

        state.restart_state = "RESTART_PENDING"
        self._write_log_banner(
            state,
            f"RESTARTING IN {decision.delay_seconds:.0f}s ({reason})",
        )
        self._sleeper(decision.delay_seconds)
        if self._stopping:
            return

        state.restart_state = "RESTARTING"
        if terminate_running:
            self._terminate_for_restart(state)

        self._restart_policy.record_restart(
            restart_times=state.restart_times,
            now=now,
        )
        state.restart_count += 1
        state.last_restart_at = datetime.now(timezone.utc)
        self._start(state, recovering=True)

    def _terminate_for_restart(
        self,
        state: ManagedProcessState,
        *,
        terminate_timeout: float = 10.0,
    ) -> None:
        process = state.process
        if process is None:
            self._close_log(state)
            return

        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=terminate_timeout)
            except (subprocess.TimeoutExpired, TimeoutError):
                process.kill()
                process.wait(timeout=5.0)

        polled = process.poll()
        state.last_exit_code = None if polled is None else int(polled)
        state.process = None
        self._write_log_banner(state, "TERMINATED FOR HEALTH RECOVERY")
        self._close_log(state)

    def _stop(
        self,
        state: ManagedProcessState,
        *,
        terminate_timeout: float,
    ) -> None:
        process = state.process
        if process is None:
            self._close_log(state)
            return

        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=terminate_timeout)
            except (subprocess.TimeoutExpired, TimeoutError):
                process.kill()
                process.wait(timeout=5.0)

        polled = process.poll()
        state.last_exit_code = None if polled is None else int(polled)
        state.process = None
        self._write_log_banner(state, "STOPPED")
        self._close_log(state)

    def _status_for(self, state: ManagedProcessState) -> ProcessStatus:
        process = state.process
        exit_code = None if process is None else process.poll()
        running = process is not None and exit_code is None
        if running:
            status = "RUNNING"
        elif state.restart_state == "FAILED":
            status = "FAILED"
        else:
            status = "STOPPED"

        return ProcessStatus(
            name=state.config.name,
            status=status,
            process_id=process.pid if running else None,
            restart_count=state.restart_count,
            restart_state=state.restart_state,
            last_restart_reason=state.last_restart_reason,
            last_restart_at=(
                None
                if state.last_restart_at is None
                else state.last_restart_at.isoformat()
            ),
            recovered_at=(
                None
                if state.recovered_at is None
                else state.recovered_at.isoformat()
            ),
            last_exit_code=state.last_exit_code,
            health=(
                None
                if state.config.name not in self._health_results
                else self._health_results[state.config.name].to_dict()
            ),
            started_at=(
                None if state.started_at is None else state.started_at.isoformat()
            ),
            log_path=str(state.config.log_path),
        )

    def _read_pid(self) -> int | None:
        try:
            return int(self._pid_path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return None

    @staticmethod
    def _process_alive(process_id: int) -> bool:
        if process_id <= 0:
            return False
        try:
            os.kill(process_id, 0)
        except OSError:
            return False
        return True

    @staticmethod
    def _write_log_banner(state: ManagedProcessState, message: str) -> None:
        if state.log_handle is None:
            return
        timestamp = datetime.now(timezone.utc).isoformat()
        state.log_handle.write(f"\n[{timestamp}] {message}\n")
        state.log_handle.flush()

    @staticmethod
    def _close_log(state: ManagedProcessState) -> None:
        if state.log_handle is not None:
            state.log_handle.close()
            state.log_handle = None


def default_processes(
    *,
    python_executable: str | None = None,
    log_directory: str | Path = "data/supervisor",
) -> list[ManagedProcessConfig]:
    python = python_executable or sys.executable
    logs = Path(log_directory)
    return [
        ManagedProcessConfig(
            name="api",
            command=(python, "run_web.py"),
            log_path=logs / "api.log",
        ),
        ManagedProcessConfig(
            name="job_worker",
            command=(python, "-m", "app.run_job_worker"),
            log_path=logs / "job_worker.log",
        ),
        ManagedProcessConfig(
            name="scheduler",
            command=(python, "-m", "app.run_scheduler"),
            log_path=logs / "scheduler.log",
        ),
    ]