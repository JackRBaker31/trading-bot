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
from urllib.error import URLError
from urllib.request import urlopen


class SpawnedProcess(Protocol):
    pid: int

    def poll(self) -> int | None: ...

    def terminate(self) -> None: ...

    def wait(self, timeout: float | None = None) -> int: ...

    def kill(self) -> None: ...


PopenFactory = Callable[..., SpawnedProcess]
Clock = Callable[[], float]
Sleeper = Callable[[float], None]
HealthProbe = Callable[[], bool]


@dataclass(frozen=True)
class ManagedProcessConfig:
    name: str
    command: tuple[str, ...]
    log_path: Path
    health_probe: HealthProbe | None = None
    startup_grace_seconds: float = 15.0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Managed process name is required.")
        if not self.command:
            raise ValueError("Managed process command is required.")
        if self.startup_grace_seconds < 0:
            raise ValueError("Startup grace cannot be negative.")


@dataclass
class ManagedProcessState:
    config: ManagedProcessConfig
    process: SpawnedProcess | None = None
    log_handle: TextIO | None = None
    started_monotonic: float | None = None
    started_at: datetime | None = None
    last_exit_code: int | None = None
    restart_count: int = 0
    consecutive_health_failures: int = 0
    last_health_ok: bool | None = None
    restart_times: deque[float] = field(default_factory=deque)


@dataclass(frozen=True)
class ProcessStatus:
    name: str
    status: str
    process_id: int | None
    restart_count: int
    last_exit_code: int | None
    health_ok: bool | None
    started_at: str | None
    log_path: str

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "process_id": self.process_id,
            "restart_count": self.restart_count,
            "last_exit_code": self.last_exit_code,
            "health_ok": self.health_ok,
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
        health_failure_limit: int = 3,
        popen_factory: PopenFactory = subprocess.Popen,
        clock: Clock = time.monotonic,
        sleeper: Sleeper = time.sleep,
    ) -> None:
        if not processes:
            raise ValueError("At least one managed process is required.")
        if check_seconds <= 0:
            raise ValueError("Check interval must be positive.")
        if max_restarts < 0:
            raise ValueError("Maximum restarts cannot be negative.")
        if restart_window_seconds <= 0:
            raise ValueError("Restart window must be positive.")
        if health_failure_limit <= 0:
            raise ValueError("Health failure limit must be positive.")

        names = [item.name for item in processes]
        if len(names) != len(set(names)):
            raise ValueError("Managed process names must be unique.")

        self._working_directory = Path(working_directory).resolve()
        self._status_path = Path(status_path)
        self._pid_path = Path(pid_path)
        self._check_seconds = check_seconds
        self._restart_enabled = restart_enabled
        self._max_restarts = max_restarts
        self._restart_window_seconds = restart_window_seconds
        self._health_failure_limit = health_failure_limit
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
            self._start(state)
        self.write_status()

    def run_once(self) -> None:
        for state in self._states.values():
            self._check(state)
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

    def _start(self, state: ManagedProcessState) -> None:
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
        state.consecutive_health_failures = 0
        state.last_health_ok = None

    def _check(self, state: ManagedProcessState) -> None:
        process = state.process
        if process is None:
            self._restart(state, reason="not running")
            return

        exit_code = process.poll()
        if exit_code is not None:
            state.last_exit_code = int(exit_code)
            self._close_log(state)
            state.process = None
            self._restart(state, reason=f"exited with code {exit_code}")
            return

        probe = state.config.health_probe
        if probe is None:
            state.last_health_ok = True
            return

        elapsed = self._clock() - (state.started_monotonic or self._clock())
        if elapsed < state.config.startup_grace_seconds:
            return

        try:
            healthy = bool(probe())
        except Exception:
            healthy = False
        state.last_health_ok = healthy
        if healthy:
            state.consecutive_health_failures = 0
            return

        state.consecutive_health_failures += 1
        if state.consecutive_health_failures < self._health_failure_limit:
            return

        self._write_log_banner(state, "HEALTH CHECK FAILED")
        self._stop(state, terminate_timeout=5.0)
        self._restart(state, reason="health check failed")

    def _restart(self, state: ManagedProcessState, *, reason: str) -> None:
        if self._stopping or not self._restart_enabled:
            return

        now = self._clock()
        while state.restart_times and (
            now - state.restart_times[0] > self._restart_window_seconds
        ):
            state.restart_times.popleft()

        if len(state.restart_times) >= self._max_restarts:
            self._write_log_banner(
                state,
                "RESTART LIMIT REACHED - MANUAL REVIEW REQUIRED",
            )
            return

        state.restart_times.append(now)
        state.restart_count += 1
        delay = min(30.0, float(2 ** min(state.restart_count - 1, 4)))
        self._write_log_banner(
            state,
            f"RESTARTING IN {delay:.0f}s ({reason})",
        )
        self._sleeper(delay)
        self._start(state)

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
        if running and state.last_health_ok is False:
            status = "UNHEALTHY"
        elif running:
            status = "RUNNING"
        elif len(state.restart_times) >= self._max_restarts:
            status = "FAILED"
        else:
            status = "STOPPED"

        return ProcessStatus(
            name=state.config.name,
            status=status,
            process_id=process.pid if running else None,
            restart_count=state.restart_count,
            last_exit_code=state.last_exit_code,
            health_ok=state.last_health_ok,
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


def http_health_probe(
    url: str,
    *,
    timeout_seconds: float = 2.0,
) -> HealthProbe:
    cleaned = url.strip()
    if not cleaned:
        raise ValueError("Health-check URL is required.")

    def probe() -> bool:
        try:
            with urlopen(cleaned, timeout=timeout_seconds) as response:
                return 200 <= int(response.status) < 300
        except (OSError, URLError, ValueError):
            return False

    return probe


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
            health_probe=http_health_probe(
                "http://127.0.0.1:8000/health/ready"
            ),
            startup_grace_seconds=15.0,
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