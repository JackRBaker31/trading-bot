from __future__ import annotations

import argparse
import json
import socket
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timezone
from os import getpid
from pathlib import Path
from typing import Iterable, Mapping

from app.health_monitor import HealthMonitor, HealthMonitorConfig
from app.worker_heartbeat_repository import WorkerHeartbeatRepository


ROOT = Path(__file__).resolve().parent
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
FRONTEND_DIR = ROOT / "frontend"
DATA_DIR = ROOT / "data"
RUNTIME_DIR = DATA_DIR / "runtime"
LOG_DIR = DATA_DIR / "logs"
DATABASE_PATH = DATA_DIR / "application.db"
STATE_PATH = RUNTIME_DIR / "kairo-launcher-state.json"
MONITOR_LOCK_PATH = RUNTIME_DIR / "kairo-monitor.json"
MONITOR_EVENTS_PATH = RUNTIME_DIR / "launcher-events.jsonl"
SUPERVISOR_STATUS_PATH = DATA_DIR / "supervisor_status.json"

API_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"

CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
CREATE_NEW_CONSOLE = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
DETACHED_PROCESS = getattr(subprocess, "DETACHED_PROCESS", 0)
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


@dataclass(frozen=True)
class ServiceDefinition:
    key: str
    display_name: str
    command: tuple[str, ...]
    cwd: Path
    port: int | None = None
    health_url: str | None = None
    process_markers: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlatformCheck:
    name: str
    status: str
    detail: str


@dataclass
class MonitoredServiceState:
    restart_times: list[float] = field(default_factory=list)
    restart_count: int = 0
    restart_state: str = "HEALTHY"
    last_restart_reason: str | None = None
    last_restart_at: str | None = None
    recovered_at: str | None = None
    frontend_failures: int = 0


SERVICES = (
    ServiceDefinition(
        key="api",
        display_name="API",
        command=(str(VENV_PYTHON), str(ROOT / "run_web.py")),
        cwd=ROOT,
        port=8000,
        health_url=f"{API_URL}/health/ready",
        process_markers=("run_web.py", "uvicorn"),
    ),
    ServiceDefinition(
        key="frontend",
        display_name="Frontend",
        command=("cmd.exe", "/d", "/c", "npm run dev"),
        cwd=FRONTEND_DIR,
        port=5173,
        health_url=FRONTEND_URL,
        process_markers=("npm run dev", "vite"),
    ),
    ServiceDefinition(
        key="worker",
        display_name="Job Worker",
        command=(str(VENV_PYTHON), "-m", "app.run_job_worker"),
        cwd=ROOT,
        process_markers=("app.run_job_worker",),
    ),
    ServiceDefinition(
        key="scheduler",
        display_name="Scheduler",
        command=(str(VENV_PYTHON), "-m", "app.run_scheduler"),
        cwd=ROOT,
        process_markers=("app.run_scheduler",),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start, stop, restart and inspect the KAIRO platform."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--status", action="store_true")
    mode.add_argument("--stop", action="store_true")
    mode.add_argument("--restart", action="store_true")
    mode.add_argument("--logs", action="store_true")
    parser.add_argument("--service", choices=tuple(item.key for item in SERVICES))
    parser.add_argument("--lines", type=int, default=40)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--foreground", action="store_true")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--monitor", action="store_true")
    parser.add_argument("--monitor-interval", type=float, default=10.0)
    parser.add_argument("--restart-delay", type=float, default=5.0)
    parser.add_argument("--restart-window", type=float, default=300.0)
    parser.add_argument("--max-restarts", type=int, default=5)
    return parser.parse_args()


def ensure_layout() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not VENV_PYTHON.exists():
        raise RuntimeError(f"Virtual-environment Python was not found at {VENV_PYTHON}.")
    if not FRONTEND_DIR.exists():
        raise RuntimeError(f"Frontend directory was not found at {FRONTEND_DIR}.")


def load_state() -> dict[str, dict[str, object]]:
    if not STATE_PATH.exists():
        return {}
    try:
        value = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(value, dict):
        return {}
    return {
        str(key): dict(item)
        for key, item in value.items()
        if isinstance(item, dict)
    }


def save_state(state: dict[str, dict[str, object]]) -> None:
    STATE_PATH.write_text(
        json.dumps(state, indent=2, sort_keys=True),
        encoding="utf-8",
    )




def append_monitor_event(
    *,
    event: str,
    service: str,
    detail: str,
    pid: int | None = None,
) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "event": event,
        "service": service,
        "detail": detail,
        "pid": pid,
    }

    with MONITOR_EVENTS_PATH.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps(
                payload,
                sort_keys=True,
            )
            + "\n"
        )


def acquire_monitor_lock() -> bool:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    if MONITOR_LOCK_PATH.exists():
        try:
            current = json.loads(
                MONITOR_LOCK_PATH.read_text(
                    encoding="utf-8"
                )
            )
        except (
            json.JSONDecodeError,
            OSError,
        ):
            current = {}

        existing_pid = current.get("pid")

        if (
            isinstance(existing_pid, int)
            and pid_is_running(existing_pid)
        ):
            return False

        MONITOR_LOCK_PATH.unlink(
            missing_ok=True
        )

    MONITOR_LOCK_PATH.write_text(
        json.dumps(
            {
                "pid": getpid(),
                "started_at": (
                    datetime.now()
                    .astimezone()
                    .isoformat()
                ),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    return True


def release_monitor_lock() -> None:
    if not MONITOR_LOCK_PATH.exists():
        return

    try:
        current = json.loads(
            MONITOR_LOCK_PATH.read_text(
                encoding="utf-8"
            )
        )
    except (
        json.JSONDecodeError,
        OSError,
    ):
        current = {}

    if current.get("pid") == getpid():
        MONITOR_LOCK_PATH.unlink(
            missing_ok=True
        )


def current_monitor_pid() -> int | None:
    if not MONITOR_LOCK_PATH.exists():
        return None
    try:
        payload = json.loads(
            MONITOR_LOCK_PATH.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError, UnicodeError):
        return None
    pid = payload.get("pid") if isinstance(payload, dict) else None
    return pid if isinstance(pid, int) and pid > 0 else None


def stop_active_monitor() -> bool:
    pid = current_monitor_pid()
    if pid is None:
        MONITOR_LOCK_PATH.unlink(missing_ok=True)
        return True
    if pid == getpid():
        return True
    if not pid_is_running(pid):
        MONITOR_LOCK_PATH.unlink(missing_ok=True)
        return True

    result = subprocess.run(
        ["taskkill", "/PID", str(pid), "/F"],
        check=False,
        capture_output=True,
        text=True,
        creationflags=CREATE_NO_WINDOW,
    )
    if result.returncode == 0:
        MONITOR_LOCK_PATH.unlink(missing_ok=True)
        return True
    return False


def _status_service_name(service: ServiceDefinition) -> str:
    return "job_worker" if service.key == "worker" else service.key


def _iso_from_epoch(value: object) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(
            float(value), tz=timezone.utc
        ).isoformat()
    except (OSError, OverflowError, ValueError):
        return None


def _service_pid(
    service: ServiceDefinition,
    state: Mapping[str, Mapping[str, object]],
) -> int | None:
    item = state.get(service.key, {})
    pid = item.get("pid")
    if isinstance(pid, int) and pid_is_running(pid):
        return pid
    matches = matching_processes(service.process_markers)
    for match in matches:
        candidate = match.get("ProcessId")
        if isinstance(candidate, int) and candidate > 0:
            return candidate
    return None


def _frontend_health(
    monitor_state: MonitoredServiceState,
) -> dict[str, object]:
    checked_at = datetime.now(timezone.utc).isoformat()
    status = url_status(FRONTEND_URL)
    healthy = status is not None and 200 <= status < 400
    if healthy:
        monitor_state.frontend_failures = 0
        detail = f"Frontend returned HTTP {status}."
        health_status = "HEALTHY"
    else:
        monitor_state.frontend_failures += 1
        detail = (
            "Frontend could not be reached."
            if status is None
            else f"Frontend returned HTTP {status}."
        )
        health_status = "UNREACHABLE"
    return {
        "name": "frontend",
        "health_status": health_status,
        "healthy": healthy,
        "persistent_fault": (
            not healthy and monitor_state.frontend_failures >= 3
        ),
        "consecutive_health_failures": monitor_state.frontend_failures,
        "last_health_check_at": checked_at,
        "last_healthy_at": checked_at if healthy else None,
        "health_detail": detail,
        "response_time_ms": None,
        "heartbeat_age_seconds": None,
        "heartbeat_status": None,
        "heartbeat_process_id": None,
        "heartbeat_last_error": None,
    }


def write_unified_supervisor_status(
    *,
    monitored: Mapping[str, MonitoredServiceState],
    health_payloads: Mapping[str, Mapping[str, object]],
    supervisor_status: str = "RUNNING",
    supervisor_process_id: int | None = None,
) -> None:
    state = clean_state(load_state())
    processes: list[dict[str, object]] = []

    for service in SERVICES:
        monitor_state = monitored.get(service.key, MonitoredServiceState())
        running = service_is_running(service, state)
        health = dict(
            health_payloads.get(
                service.key,
                {
                    "name": _status_service_name(service),
                    "health_status": "UNKNOWN",
                    "healthy": running,
                    "persistent_fault": False,
                    "consecutive_health_failures": 0,
                    "last_health_check_at": datetime.now(timezone.utc).isoformat(),
                    "last_healthy_at": None,
                    "health_detail": "No health result was available.",
                },
            )
        )
        if not running:
            health.update(
                {
                    "healthy": False,
                    "health_status": "STOPPED",
                    "persistent_fault": True,
                    "health_detail": f"{service.display_name} process was not detected.",
                }
            )

        process_status = "RUNNING" if running else "STOPPED"
        if monitor_state.restart_state == "FAILED":
            process_status = "FAILED"

        item = state.get(service.key, {})
        processes.append(
            {
                "name": _status_service_name(service),
                "status": process_status,
                "process_id": _service_pid(service, state),
                "restart_count": monitor_state.restart_count,
                "restart_state": monitor_state.restart_state,
                "last_restart_reason": monitor_state.last_restart_reason,
                "last_restart_at": monitor_state.last_restart_at,
                "recovered_at": monitor_state.recovered_at,
                "last_exit_code": None,
                "health": health,
                "started_at": _iso_from_epoch(item.get("started_at")),
                "log_path": str(LOG_DIR / f"{service.key}.log"),
            }
        )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "supervisor_status": supervisor_status.upper(),
        "supervisor_process_id": (
            getpid() if supervisor_process_id is None else supervisor_process_id
        ),
        "restart_enabled": supervisor_status.upper() != "STOPPED",
        "supervisor_type": "KAIRO_UNIFIED_LAUNCHER",
        "processes": processes,
    }
    SUPERVISOR_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = SUPERVISOR_STATUS_PATH.with_suffix(
        SUPERVISOR_STATUS_PATH.suffix + ".tmp"
    )
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    temporary.replace(SUPERVISOR_STATUS_PATH)


def write_stopped_supervisor_status() -> None:
    monitored = {service.key: MonitoredServiceState() for service in SERVICES}
    health = {
        service.key: {
            "name": _status_service_name(service),
            "health_status": "STOPPED",
            "healthy": False,
            "persistent_fault": False,
            "consecutive_health_failures": 0,
            "last_health_check_at": datetime.now(timezone.utc).isoformat(),
            "last_healthy_at": None,
            "health_detail": "Platform supervision is stopped.",
        }
        for service in SERVICES
    }
    write_unified_supervisor_status(
        monitored=monitored,
        health_payloads=health,
        supervisor_status="STOPPED",
        supervisor_process_id=0,
    )


def trim_restart_history(
    restart_times: list[float],
    *,
    now: float,
    window_seconds: float,
) -> list[float]:
    cutoff = now - window_seconds

    return [
        timestamp
        for timestamp in restart_times
        if timestamp >= cutoff
    ]


def pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    result = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
        check=False,
        capture_output=True,
        text=True,
        creationflags=CREATE_NO_WINDOW,
    )
    output = result.stdout.strip()
    return bool(output) and "No tasks are running" not in output


def clean_state(
    state: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    cleaned = {
        key: item
        for key, item in state.items()
        if isinstance(item.get("pid"), int)
        and pid_is_running(int(item["pid"]))
    }
    if cleaned != state:
        save_state(cleaned)
    return cleaned


def port_is_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.settimeout(0.5)
        return connection.connect_ex((host, port)) == 0


def url_status(url: str, timeout: float = 1.5) -> int | None:
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "KAIRO-Launcher/2.0"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def url_is_healthy(url: str) -> bool:
    status = url_status(url)
    return status is not None and 200 <= status < 500


def matching_processes(markers: Iterable[str]) -> list[dict[str, object]]:
    conditions = " -or ".join(
        "$_.CommandLine -match " + repr(marker)
        for marker in markers
    )
    script = (
        "$currentPid = $PID; "
        "$items = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | "
        "Where-Object { "
        "$_.ProcessId -ne $currentPid -and $_.CommandLine "
        "-and $_.Name -notmatch 'powershell|pwsh' -and ("
        + conditions
        + ") }; "
        "$items | Select-Object ProcessId,ParentProcessId,Name,CommandLine "
        "| ConvertTo-Json -Compress"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", script],
        check=False,
        capture_output=True,
        text=True,
        creationflags=CREATE_NO_WINDOW,
    )
    output = result.stdout.strip()
    if not output:
        return []
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, dict):
        return [parsed]
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    return []


def service_is_running(
    service: ServiceDefinition,
    state: Mapping[str, Mapping[str, object]],
) -> bool:
    if service.port is not None and port_is_open(service.port):
        return True
    item = state.get(service.key, {})
    pid = item.get("pid")
    if isinstance(pid, int) and pid_is_running(pid):
        return True
    return bool(matching_processes(service.process_markers))


def service_health(
    service: ServiceDefinition,
    state: Mapping[str, Mapping[str, object]],
) -> str:
    if not service_is_running(service, state):
        return "STOPPED"
    if service.health_url:
        return "HEALTHY" if url_is_healthy(service.health_url) else "STARTING"
    return "RUNNING"


def start_service(
    service: ServiceDefinition,
    *,
    foreground: bool,
) -> subprocess.Popen[bytes]:
    if foreground:
        if service.key == "frontend":
            return subprocess.Popen(
                ["cmd.exe", "/d", "/k", "npm run dev"],
                cwd=service.cwd,
                creationflags=CREATE_NEW_CONSOLE | CREATE_NEW_PROCESS_GROUP,
            )
        return subprocess.Popen(
            service.command,
            cwd=service.cwd,
            creationflags=CREATE_NEW_CONSOLE | CREATE_NEW_PROCESS_GROUP,
        )

    stdout = (LOG_DIR / f"{service.key}.log").open("ab", buffering=0)
    stderr = (LOG_DIR / f"{service.key}.error.log").open("ab", buffering=0)
    return subprocess.Popen(
        service.command,
        cwd=service.cwd,
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
        creationflags=CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS,
        close_fds=True,
    )


def wait_for_service(
    service: ServiceDefinition,
    *,
    timeout_seconds: int,
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if service.health_url and url_is_healthy(service.health_url):
            return True
        if not service.health_url and service.port is not None and port_is_open(service.port):
            return True
        if service.health_url is None and service.port is None:
            return True
        time.sleep(1)
    return False


def stop_pid(pid: int) -> bool:
    if not pid_is_running(pid):
        return True
    result = subprocess.run(
        ["taskkill", "/PID", str(pid), "/T", "/F"],
        check=False,
        capture_output=True,
        text=True,
        creationflags=CREATE_NO_WINDOW,
    )
    return result.returncode == 0


def stop_managed_services() -> int:
    ensure_layout()

    monitor_stopped = stop_active_monitor()
    if not monitor_stopped:
        print("[FAIL] Platform Supervisor could not be stopped.")
        return 1
    time.sleep(0.5)

    state = clean_state(load_state())
    if not state:
        print("No launcher-managed services were found.")
        write_stopped_supervisor_status()
        return 0

    failures = 0
    for service in reversed(SERVICES):
        item = state.get(service.key, {})
        pid = item.get("pid")
        if not isinstance(pid, int):
            print(f"[SKIP] {service.display_name}: not launcher-managed.")
            continue
        print(f"[STOP] {service.display_name} (PID {pid})")
        if stop_pid(pid):
            print(f"[OK]   {service.display_name} stopped.")
        else:
            failures += 1
            print(f"[FAIL] {service.display_name} could not be stopped.")

    if failures == 0:
        STATE_PATH.unlink(missing_ok=True)
    write_stopped_supervisor_status()
    return 1 if failures else 0


def database_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def find_table(
    connection: sqlite3.Connection,
    required_columns: set[str],
) -> str | None:
    tables = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
    ).fetchall()
    for table in tables:
        name = str(table["name"])
        columns = {
            str(row["name"])
            for row in connection.execute(
                f'PRAGMA table_info("{name}")'
            ).fetchall()
        }
        if required_columns.issubset(columns):
            return name
    return None


def platform_checks() -> tuple[PlatformCheck, ...]:
    checks = [
        PlatformCheck(
            "Virtual environment",
            "OK" if VENV_PYTHON.exists() else "FAILED",
            str(VENV_PYTHON),
        ),
        PlatformCheck(
            "Frontend project",
            "OK" if (FRONTEND_DIR / "package.json").exists() else "FAILED",
            str(FRONTEND_DIR),
        ),
        PlatformCheck(
            "Database",
            "OK" if DATABASE_PATH.exists() else "FAILED",
            str(DATABASE_PATH),
        ),
    ]
    watchlist = DATA_DIR / "watchlists" / "core_universe.txt"
    if watchlist.exists():
        symbols = [
            line.strip()
            for line in watchlist.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        checks.append(PlatformCheck("Core universe", "OK", f"{len(symbols)} symbol(s)"))
    else:
        checks.append(PlatformCheck("Core universe", "FAILED", f"Missing: {watchlist}"))
    return tuple(checks)


def latest_intelligence_job() -> dict[str, object] | None:
    if not DATABASE_PATH.exists():
        return None
    with database_connection() as connection:
        table = find_table(
            connection,
            {
                "job_id", "job_type", "status", "created_at",
                "started_at", "finished_at", "result_json",
            },
        )
        if table is None:
            return None
        columns = {
            str(row["name"])
            for row in connection.execute(
                f'PRAGMA table_info("{table}")'
            ).fetchall()
        }
        optional = []
        if "error_code" in columns:
            optional.append("error_code")
        if "error_summary" in columns:
            optional.append("error_summary")
        select_optional = ", " + ", ".join(optional) if optional else ""
        row = connection.execute(
            f"""
            SELECT
                job_id,
                status,
                created_at,
                started_at,
                finished_at,
                result_json
                {select_optional}
            FROM "{table}"
            WHERE job_type = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            ("INTELLIGENCE_CYCLE",),
        ).fetchone()
        if row is None:
            return None

        result: dict[str, object] = {}
        if row["result_json"]:
            try:
                parsed = json.loads(str(row["result_json"]))
                if isinstance(parsed, dict):
                    result = parsed
            except json.JSONDecodeError:
                pass

        return {
            "job_id": str(row["job_id"]),
            "status": str(row["status"]),
            "created_at": str(row["created_at"]),
            "started_at": str(row["started_at"]) if row["started_at"] is not None else None,
            "finished_at": str(row["finished_at"]) if row["finished_at"] is not None else None,
            "result": result,
            "error_code": (
                str(row["error_code"])
                if "error_code" in columns and row["error_code"] is not None
                else None
            ),
            "error_summary": (
                str(row["error_summary"])
                if "error_summary" in columns and row["error_summary"] is not None
                else None
            ),
        }


def next_intelligence_schedule() -> dict[str, object] | None:
    if not DATABASE_PATH.exists():
        return None
    with database_connection() as connection:
        table = find_table(
            connection,
            {"schedule_id", "task_type", "enabled", "next_run_at", "payload_json"},
        )
        if table is None:
            return None
        columns = {
            str(row["name"])
            for row in connection.execute(
                f'PRAGMA table_info("{table}")'
            ).fetchall()
        }
        available = [
            name
            for name in ("last_run_at", "last_status", "created_at")
            if name in columns
        ]
        optional = ", " + ", ".join(available) if available else ""
        order = "created_at ASC" if "created_at" in columns else "schedule_id ASC"
        row = connection.execute(
            f"""
            SELECT
                schedule_id,
                enabled,
                next_run_at,
                payload_json
                {optional}
            FROM "{table}"
            WHERE task_type = ?
            ORDER BY {order}
            LIMIT 1
            """,
            ("INTELLIGENCE_CYCLE",),
        ).fetchone()
        if row is None:
            return None

        payload: dict[str, object] = {}
        try:
            parsed = json.loads(str(row["payload_json"]))
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            pass

        return {
            "schedule_id": str(row["schedule_id"]),
            "enabled": bool(row["enabled"]),
            "next_run_at": str(row["next_run_at"]) if row["next_run_at"] is not None else None,
            "last_run_at": (
                str(row["last_run_at"])
                if "last_run_at" in columns and row["last_run_at"] is not None
                else None
            ),
            "last_status": (
                str(row["last_status"])
                if "last_status" in columns and row["last_status"] is not None
                else None
            ),
            "payload": payload,
        }


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    cleaned = value.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def duration_seconds(
    started_at: str | None,
    finished_at: str | None,
) -> float | None:
    started = parse_iso(started_at)
    finished = parse_iso(finished_at)
    if started is None or finished is None:
        return None
    return round((finished - started).total_seconds(), 2)


def stage_detail(
    job: Mapping[str, object],
    stage_name: str,
) -> dict[str, object]:
    result = job.get("result", {})
    if not isinstance(result, Mapping):
        return {}
    stages = result.get("stages", ())
    if not isinstance(stages, list):
        return {}
    for stage in stages:
        if isinstance(stage, Mapping) and stage.get("stage") == stage_name:
            detail = stage.get("detail", {})
            return dict(detail) if isinstance(detail, Mapping) else {}
    return {}


def count_warnings(job: Mapping[str, object]) -> int:
    result = job.get("result", {})
    if not isinstance(result, Mapping):
        return 0
    stages = result.get("stages", ())
    if not isinstance(stages, list):
        return 0
    return sum(
        len(stage.get("warnings", ()))
        for stage in stages
        if isinstance(stage, Mapping)
        and isinstance(stage.get("warnings", ()), list)
    )


def divider(title: str) -> None:
    print()
    print(title)
    print("-" * 58)


def supervisor_cli_status() -> str:
    if not SUPERVISOR_STATUS_PATH.exists():
        return "NOT_SEEN"
    try:
        payload = json.loads(
            SUPERVISOR_STATUS_PATH.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError, UnicodeError):
        return "FAILED"
    if not isinstance(payload, dict):
        return "FAILED"

    recorded = str(payload.get("supervisor_status") or "UNKNOWN").upper()
    if recorded == "STOPPED":
        return "STOPPED"

    process_id = payload.get("supervisor_process_id")
    generated_at = parse_iso(str(payload.get("generated_at") or ""))
    stale = True
    if generated_at is not None:
        now = datetime.now(generated_at.tzinfo or timezone.utc)
        stale = (now - generated_at).total_seconds() > 30.0
    alive = isinstance(process_id, int) and pid_is_running(process_id)
    if stale or not alive:
        return "STALE"
    return recorded


def print_detailed_status() -> int:
    ensure_layout()
    state = clean_state(load_state())

    print("=" * 58)
    print("KAIRO PLATFORM CONTROL CENTRE")
    print("=" * 58)

    all_running = True
    divider("Services")
    supervisor_status = supervisor_cli_status()
    all_running = all_running and supervisor_status == "RUNNING"
    print(f"{'Platform Supervisor':<22}{supervisor_status}")
    for service in SERVICES:
        status = service_health(service, state)
        all_running = all_running and status != "STOPPED"
        print(f"{service.display_name:<22}{status}")

    divider("Infrastructure")
    for check in platform_checks():
        print(f"{check.name:<22}{check.status:<10}{check.detail}")

    job = latest_intelligence_job()
    divider("Latest Intelligence Cycle")
    if job is None:
        print("No Intelligence Cycle record was found.")
    else:
        duration = duration_seconds(
            job.get("started_at"),
            job.get("finished_at"),
        )
        news = stage_detail(job, "NEWS_RESEARCH")
        shadow = stage_detail(job, "SHADOW_ANALYSIS")
        outcomes = stage_detail(job, "CAPTURE_PRICE_OUTCOMES")
        print(f"{'Status':<22}{job['status']}")
        print(f"{'Job ID':<22}{job['job_id']}")
        print(
            f"{'Duration':<22}"
            + (f"{duration:.2f} seconds" if duration is not None else "—")
        )
        print(f"{'Articles fetched':<22}{news.get('articles_fetched', '—')}")
        print(f"{'Signals stored':<22}{news.get('signals_stored', '—')}")
        print(f"{'Opportunities':<22}{shadow.get('opportunities_seen', '—')}")
        print(f"{'Outcomes recorded':<22}{outcomes.get('outcomes_recorded', '—')}")
        print(f"{'Warnings':<22}{count_warnings(job)}")
        if job.get("error_code"):
            print(
                f"{'Error':<22}{job['error_code']}: "
                f"{job.get('error_summary') or ''}"
            )

    schedule = next_intelligence_schedule()
    divider("Schedule")
    if schedule is None:
        print("No Intelligence Cycle schedule was found.")
    else:
        payload = schedule.get("payload", {})
        if not isinstance(payload, Mapping):
            payload = {}
        print(f"{'Enabled':<22}{schedule['enabled']}")
        print(f"{'Next run':<22}{schedule['next_run_at'] or '—'}")
        print(f"{'Last status':<22}{schedule['last_status'] or '—'}")
        print(f"{'Watchlist':<22}{payload.get('watchlist_path', '—')}")
        print(f"{'Provider':<22}{payload.get('provider', '—')}")

    divider("Dashboard")
    print(FRONTEND_URL)
    print("=" * 58)
    return 0 if all_running else 1


def tail_file(path: Path, lines: int) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines()[-lines:]


def show_logs(service_key: str | None, lines: int) -> int:
    ensure_layout()
    selected = [
        service
        for service in SERVICES
        if service_key is None or service.key == service_key
    ]
    for service in selected:
        print("=" * 58)
        print(f"{service.display_name} LOGS")
        print("=" * 58)
        any_content = False
        for label, path in (
            ("Output", LOG_DIR / f"{service.key}.log"),
            ("Errors", LOG_DIR / f"{service.key}.error.log"),
        ):
            content = tail_file(path, lines)
            if not content:
                continue
            any_content = True
            print()
            print(label)
            print("-" * 58)
            for line in content:
                print(line)
        if not any_content:
            print("No background-mode logs were found.")
        print()
    return 0


def start_platform(
    *,
    foreground: bool,
    no_browser: bool,
    timeout_seconds: int,
) -> int:
    ensure_layout()
    state = clean_state(load_state())
    changed = False

    print("=" * 58)
    print("KAIRO SMART LAUNCHER V2")
    print("=" * 58)

    for service in SERVICES:
        if service_is_running(service, state):
            print(f"[OK]    {service.display_name} already running.")
            continue

        print(f"[START] {service.display_name}")
        try:
            process = start_service(service, foreground=foreground)
        except OSError as error:
            print(f"[FAIL]  {service.display_name}: {error}")
            continue

        state[service.key] = {
            "pid": process.pid,
            "started_at": time.time(),
            "foreground": foreground,
            "command": list(service.command),
        }
        save_state(state)
        changed = True

        if service.health_url is not None or service.port is not None:
            print(f"[WAIT]  Waiting for {service.display_name}...")
            if wait_for_service(service, timeout_seconds=timeout_seconds):
                print(f"[READY] {service.display_name}")
            else:
                print(
                    f"[WARN]  {service.display_name} did not become ready "
                    f"within {timeout_seconds} seconds."
                )
        else:
            time.sleep(1)

    print("=" * 58)
    if changed:
        print("Missing KAIRO services were started.")
    else:
        print("All KAIRO services were already running. Nothing to start.")

    if url_is_healthy(FRONTEND_URL):
        print(f"Dashboard: {FRONTEND_URL}")
        if not no_browser:
            webbrowser.open(FRONTEND_URL, new=2)
            print("Dashboard opened in the browser.")
    else:
        print("Frontend is not ready. The browser was not opened.")

    print("=" * 58)
    return 0



def monitor_platform(
    *,
    foreground: bool,
    interval_seconds: float,
    restart_delay_seconds: float,
    restart_window_seconds: float,
    max_restarts: int,
) -> int:
    if interval_seconds <= 0:
        raise RuntimeError("Monitor interval must be positive.")
    if restart_delay_seconds < 0:
        raise RuntimeError("Restart delay cannot be negative.")
    if restart_window_seconds <= 0:
        raise RuntimeError("Restart window must be positive.")
    if max_restarts <= 0:
        raise RuntimeError("Maximum restarts must be positive.")

    if not acquire_monitor_lock():
        print("[MONITOR] Another KAIRO Platform Supervisor is already active.")
        return 0

    heartbeat_repository = WorkerHeartbeatRepository(
        database_path=str(DATABASE_PATH),
    )
    heartbeat_repository.initialize()
    health_monitor = HealthMonitor(
        heartbeat_repository=heartbeat_repository,
        config=HealthMonitorConfig(
            api_url=f"{API_URL}/health/ready",
            startup_grace_seconds=20.0,
            heartbeat_stale_seconds=30.0,
            persistent_failure_count=3,
        ),
    )
    monitored = {
        service.key: MonitoredServiceState()
        for service in SERVICES
    }
    latest_health: dict[str, Mapping[str, object]] = {}

    print()
    print("=" * 58)
    print("KAIRO PLATFORM SUPERVISOR ACTIVE")
    print("=" * 58)
    print(
        "Monitoring API, Frontend, Job Worker and Scheduler every "
        f"{interval_seconds:g} seconds."
    )
    print(
        "Restart policy: "
        f"{max_restarts} restart(s) per service within "
        f"{restart_window_seconds:g} seconds."
    )
    print("Keep this window open. Ctrl+C stops supervision only.")
    print("=" * 58)

    append_monitor_event(
        event="MONITOR_STARTED",
        service="platform",
        detail=(
            "Unified launcher supervision started for API, Frontend, "
            "Job Worker and Scheduler."
        ),
        pid=getpid(),
    )

    try:
        while True:
            launcher_state = clean_state(load_state())
            raw_health = health_monitor.check_all()
            latest_health = {
                "api": raw_health["api"].to_dict(),
                "worker": raw_health["job_worker"].to_dict(),
                "scheduler": raw_health["scheduler"].to_dict(),
                "frontend": _frontend_health(monitored["frontend"]),
            }

            for service in SERVICES:
                service_state = monitored[service.key]
                running = service_is_running(service, launcher_state)
                health = latest_health[service.key]
                healthy = bool(health.get("healthy", False))

                item = launcher_state.get(service.key, {})
                started_at = item.get("started_at")
                in_startup_grace = (
                    isinstance(started_at, (int, float))
                    and time.time() - float(started_at) < 20.0
                )

                if running and healthy:
                    if service_state.restart_state in {
                        "RESTART_PENDING",
                        "RESTARTING",
                        "RECOVERING",
                        "FAULT_DETECTED",
                    }:
                        service_state.restart_state = "RECOVERED"
                        service_state.recovered_at = (
                            datetime.now(timezone.utc).isoformat()
                        )
                        append_monitor_event(
                            event="SERVICE_RECOVERED",
                            service=service.key,
                            detail=(
                                f"{service.display_name} passed its health check "
                                "after recovery."
                            ),
                            pid=_service_pid(service, launcher_state),
                        )
                    elif service_state.restart_state != "FAILED":
                        service_state.restart_state = "HEALTHY"
                    continue

                if service_state.restart_state == "FAILED":
                    continue

                if running and in_startup_grace:
                    service_state.restart_state = "RECOVERING"
                    continue

                persistent_fault = (
                    not running
                    or bool(health.get("persistent_fault", False))
                )
                if not persistent_fault:
                    service_state.restart_state = "FAULT_DETECTED"
                    continue

                reason = (
                    f"{service.display_name} process was not detected."
                    if not running
                    else str(
                        health.get("health_detail")
                        or f"{service.display_name} failed its health check."
                    )
                )
                event_name = "SERVICE_LOST" if not running else "HEALTH_FAULT"
                append_monitor_event(
                    event=event_name,
                    service=service.key,
                    detail=reason,
                    pid=_service_pid(service, launcher_state),
                )

                now = time.monotonic()
                service_state.restart_times = trim_restart_history(
                    service_state.restart_times,
                    now=now,
                    window_seconds=restart_window_seconds,
                )
                if len(service_state.restart_times) >= max_restarts:
                    service_state.restart_state = "FAILED"
                    service_state.last_restart_reason = reason
                    detail = (
                        f"Restart limit reached for {service.display_name}: "
                        f"{len(service_state.restart_times)} restart(s) within "
                        f"{restart_window_seconds:g} seconds."
                    )
                    print(f"[GIVE UP] {detail}")
                    append_monitor_event(
                        event="RESTART_LIMIT_REACHED",
                        service=service.key,
                        detail=detail,
                    )
                    continue

                if running:
                    owned_pid = item.get("pid")
                    if not isinstance(owned_pid, int) or not pid_is_running(owned_pid):
                        service_state.restart_state = "FAILED"
                        service_state.last_restart_reason = (
                            "Persistent health fault belongs to a process that "
                            "was not launched by the unified supervisor."
                        )
                        append_monitor_event(
                            event="UNMANAGED_PROCESS_FAULT",
                            service=service.key,
                            detail=service_state.last_restart_reason,
                            pid=_service_pid(service, launcher_state),
                        )
                        continue
                    if not stop_pid(owned_pid):
                        service_state.restart_state = "FAILED"
                        service_state.last_restart_reason = (
                            f"{service.display_name} could not be stopped for recovery."
                        )
                        append_monitor_event(
                            event="RESTART_FAILED",
                            service=service.key,
                            detail=service_state.last_restart_reason,
                            pid=owned_pid,
                        )
                        continue
                    launcher_state.pop(service.key, None)
                    save_state(launcher_state)

                service_state.restart_state = "RESTART_PENDING"
                service_state.last_restart_reason = reason
                write_unified_supervisor_status(
                    monitored=monitored,
                    health_payloads=latest_health,
                    supervisor_status="DEGRADED",
                )

                if restart_delay_seconds:
                    print(
                        f"[MONITOR] Restarting {service.display_name} in "
                        f"{restart_delay_seconds:g} seconds..."
                    )
                    time.sleep(restart_delay_seconds)

                try:
                    process = start_service(service, foreground=foreground)
                except OSError as error:
                    service_state.restart_times.append(time.monotonic())
                    service_state.restart_state = "RESTARTING"
                    service_state.last_restart_reason = str(error)
                    print(
                        f"[RESTART FAILED] {service.display_name}: {error}"
                    )
                    append_monitor_event(
                        event="RESTART_FAILED",
                        service=service.key,
                        detail=f"{service.display_name} restart failed: {error}",
                    )
                    continue

                launcher_state = clean_state(load_state())
                launcher_state[service.key] = {
                    "pid": process.pid,
                    "started_at": time.time(),
                    "foreground": foreground,
                    "command": list(service.command),
                    "restart_reason": "unified_supervisor_recovery",
                }
                save_state(launcher_state)

                service_state.restart_times.append(time.monotonic())
                service_state.restart_count += 1
                service_state.restart_state = "RECOVERING"
                service_state.last_restart_at = (
                    datetime.now(timezone.utc).isoformat()
                )
                print(
                    f"[RECOVERING] {service.display_name} restarted "
                    f"(PID {process.pid})."
                )
                append_monitor_event(
                    event="SERVICE_RESTARTED",
                    service=service.key,
                    detail=f"{service.display_name} restarted successfully.",
                    pid=process.pid,
                )

            states = {item.restart_state for item in monitored.values()}
            if "FAILED" in states:
                supervisor_status = "FAILED"
            elif states.intersection(
                {"FAULT_DETECTED", "RESTART_PENDING", "RESTARTING", "RECOVERING"}
            ):
                supervisor_status = "DEGRADED"
            else:
                supervisor_status = "RUNNING"

            write_unified_supervisor_status(
                monitored=monitored,
                health_payloads=latest_health,
                supervisor_status=supervisor_status,
            )
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print()
        print(
            "[MONITOR] Platform supervision stopped. "
            "KAIRO services remain running."
        )
        append_monitor_event(
            event="MONITOR_STOPPED",
            service="platform",
            detail="Unified platform supervision was stopped manually.",
            pid=getpid(),
        )
        write_unified_supervisor_status(
            monitored=monitored,
            health_payloads=latest_health,
            supervisor_status="STOPPED",
        )
        return 0
    except Exception as error:
        append_monitor_event(
            event="MONITOR_FAILED",
            service="platform",
            detail=f"Unified supervisor failed: {type(error).__name__}: {error}",
            pid=getpid(),
        )
        write_unified_supervisor_status(
            monitored=monitored,
            health_payloads=latest_health,
            supervisor_status="FAILED",
        )
        raise
    finally:
        release_monitor_lock()



def main() -> int:
    args = parse_args()
    try:
        if args.stop:
            return stop_managed_services()
        if args.restart:
            result = stop_managed_services()
            if result != 0:
                return result
            time.sleep(2)
            result = start_platform(
                foreground=args.foreground,
                no_browser=args.no_browser,
                timeout_seconds=args.timeout,
            )
            if result != 0 or not args.monitor:
                return result
            return monitor_platform(
                foreground=args.foreground,
                interval_seconds=args.monitor_interval,
                restart_delay_seconds=args.restart_delay,
                restart_window_seconds=args.restart_window,
                max_restarts=args.max_restarts,
            )
        if args.status:
            return print_detailed_status()
        if args.logs:
            return show_logs(args.service, max(args.lines, 1))
        result = start_platform(
            foreground=args.foreground,
            no_browser=args.no_browser,
            timeout_seconds=args.timeout,
        )

        if result != 0 or not args.monitor:
            return result

        return monitor_platform(
            foreground=args.foreground,
            interval_seconds=(
                args.monitor_interval
            ),
            restart_delay_seconds=(
                args.restart_delay
            ),
            restart_window_seconds=(
                args.restart_window
            ),
            max_restarts=(
                args.max_restarts
            ),
        )
    except RuntimeError as error:
        print(f"KAIRO launcher error: {error}")
        return 1
    except KeyboardInterrupt:
        print("\nLauncher interrupted.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
