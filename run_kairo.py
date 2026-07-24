from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
FRONTEND_DIR = ROOT / "frontend"
RUNTIME_DIR = ROOT / "data" / "runtime"
LOG_DIR = ROOT / "data" / "logs"
STATE_PATH = RUNTIME_DIR / "kairo-launcher-state.json"

API_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"

CREATE_NEW_CONSOLE = getattr(
    subprocess,
    "CREATE_NEW_CONSOLE",
    0,
)

CREATE_NEW_PROCESS_GROUP = getattr(
    subprocess,
    "CREATE_NEW_PROCESS_GROUP",
    0,
)
DETACHED_PROCESS = getattr(
    subprocess,
    "DETACHED_PROCESS",
    0,
)
CREATE_NO_WINDOW = getattr(
    subprocess,
    "CREATE_NO_WINDOW",
    0,
)


@dataclass(frozen=True)
class ServiceDefinition:
    key: str
    display_name: str
    command: tuple[str, ...]
    cwd: Path
    port: int | None = None
    health_url: str | None = None
    process_markers: tuple[str, ...] = ()


SERVICES = (
    ServiceDefinition(
        key="api",
        display_name="API",
        command=(
            str(VENV_PYTHON),
            str(ROOT / "run_web.py"),
        ),
        cwd=ROOT,
        port=8000,
        health_url=f"{API_URL}/health/ready",
        process_markers=(
            "run_web.py",
            "uvicorn",
        ),
    ),
    ServiceDefinition(
        key="frontend",
        display_name="Frontend",
        command=(
            "cmd.exe",
            "/d",
            "/c",
            "npm run dev",
        ),
        cwd=FRONTEND_DIR,
        port=5173,
        health_url=FRONTEND_URL,
        process_markers=(
            "npm run dev",
            "vite",
        ),
    ),
    ServiceDefinition(
        key="worker",
        display_name="Job Worker",
        command=(
            str(VENV_PYTHON),
            "-m",
            "app.run_job_worker",
        ),
        cwd=ROOT,
        process_markers=(
            "app.run_job_worker",
        ),
    ),
    ServiceDefinition(
        key="scheduler",
        display_name="Scheduler",
        command=(
            str(VENV_PYTHON),
            "-m",
            "app.run_scheduler",
        ),
        cwd=ROOT,
        process_markers=(
            "app.run_scheduler",
        ),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Start, stop, restart and inspect the "
            "KAIRO development platform."
        )
    )
    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "--status",
        action="store_true",
        help="Show current platform status.",
    )
    group.add_argument(
        "--stop",
        action="store_true",
        help="Stop launcher-managed services.",
    )
    group.add_argument(
        "--restart",
        action="store_true",
        help="Restart the platform.",
    )

    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open the frontend in a browser.",
    )
    parser.add_argument(
        "--foreground",
        action="store_true",
        help=(
            "Open each service in its own visible "
            "persistent command window."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Startup health-check timeout in seconds.",
    )

    return parser.parse_args()


def ensure_layout() -> None:
    RUNTIME_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not VENV_PYTHON.exists():
        raise RuntimeError(
            "Virtual-environment Python was not found at "
            f"{VENV_PYTHON}."
        )

    if not FRONTEND_DIR.exists():
        raise RuntimeError(
            "Frontend directory was not found at "
            f"{FRONTEND_DIR}."
        )


def load_state() -> dict[str, dict[str, object]]:
    if not STATE_PATH.exists():
        return {}

    try:
        raw = json.loads(
            STATE_PATH.read_text(
                encoding="utf-8"
            )
        )
    except (
        json.JSONDecodeError,
        OSError,
    ):
        return {}

    if not isinstance(raw, dict):
        return {}

    return {
        str(key): dict(value)
        for key, value in raw.items()
        if isinstance(value, dict)
    }


def save_state(
    state: dict[str, dict[str, object]],
) -> None:
    STATE_PATH.write_text(
        json.dumps(
            state,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False

    try:
        process = subprocess.run(
            [
                "tasklist",
                "/FI",
                f"PID eq {pid}",
                "/FO",
                "CSV",
                "/NH",
            ],
            check=False,
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW,
        )
    except OSError:
        return False

    output = process.stdout.strip()

    return (
        bool(output)
        and "No tasks are running" not in output
    )


def port_is_open(
    port: int,
    host: str = "127.0.0.1",
) -> bool:
    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as connection:
        connection.settimeout(0.5)
        return (
            connection.connect_ex(
                (host, port)
            )
            == 0
        )


def url_is_healthy(
    url: str,
    timeout: float = 1.5,
) -> bool:
    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "KAIRO-Launcher/1.0"
                )
            },
        )
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            return 200 <= response.status < 500
    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
    ):
        return False

def matching_processes(
    markers: Iterable[str],
) -> list[dict[str, object]]:
    marker_conditions = " -or ".join(
        (
            "$_.CommandLine -match "
            + repr(marker)
        )
        for marker in markers
    )

    script = (
        "$currentPid = $PID; "
        "$items = Get-CimInstance "
        "Win32_Process "
        "-ErrorAction SilentlyContinue | "
        "Where-Object { "
        "$_.ProcessId -ne $currentPid "
        "-and $_.CommandLine "
        "-and ("
        + marker_conditions
        + ") "
        "-and $_.Name -notmatch "
        "'powershell|pwsh' "
        "}; "
        "$items | Select-Object "
        "ProcessId,ParentProcessId,"
        "Name,CommandLine "
        "| ConvertTo-Json -Compress"
    )

    process = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            script,
        ],
        check=False,
        capture_output=True,
        text=True,
        creationflags=CREATE_NO_WINDOW,
    )

    output = process.stdout.strip()

    if not output:
        return []

    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        return []

    if isinstance(parsed, dict):
        return [parsed]

    if isinstance(parsed, list):
        return [
            item
            for item in parsed
            if isinstance(item, dict)
        ]

    return []

def service_is_running(
    service: ServiceDefinition,
    state: dict[str, dict[str, object]],
) -> bool:
    if (
        service.port is not None
        and port_is_open(service.port)
    ):
        return True

    state_item = state.get(
        service.key,
        {},
    )
    pid = state_item.get("pid")

    if isinstance(pid, int) and pid_is_running(pid):
        return True

    return bool(
        matching_processes(
            service.process_markers
        )
    )


def visible_command(
    service: ServiceDefinition,
) -> list[str]:
    command = subprocess.list2cmdline(
        list(service.command)
    )

    return [
        "cmd.exe",
        "/d",
        "/k",
        (
            f'cd /d "{service.cwd}" '
            f"&& {command}"
        ),
    ]


def start_service(
    service: ServiceDefinition,
    *,
    foreground: bool,
) -> subprocess.Popen[bytes]:
    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if foreground:
        # The frontend must run through CMD because
        # npm is normally exposed as npm.cmd.
        if service.key == "frontend":
            return subprocess.Popen(
                [
                    "cmd.exe",
                    "/d",
                    "/k",
                    "npm run dev",
                ],
                cwd=service.cwd,
                creationflags=(
                    CREATE_NEW_CONSOLE
                    | CREATE_NEW_PROCESS_GROUP
                ),
            )

        # Start Python services directly in their own
        # console. This avoids nested CMD quoting.
        return subprocess.Popen(
            service.command,
            cwd=service.cwd,
            creationflags=(
                CREATE_NEW_CONSOLE
                | CREATE_NEW_PROCESS_GROUP
            ),
        )

    stdout_path = (
        LOG_DIR
        / f"{service.key}.log"
    )
    stderr_path = (
        LOG_DIR
        / f"{service.key}.error.log"
    )

    stdout = stdout_path.open(
        "ab",
        buffering=0,
    )
    stderr = stderr_path.open(
        "ab",
        buffering=0,
    )

    return subprocess.Popen(
        service.command,
        cwd=service.cwd,
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
        creationflags=(
            CREATE_NEW_PROCESS_GROUP
            | DETACHED_PROCESS
        ),
        close_fds=True,
    )

def wait_for_service(
    service: ServiceDefinition,
    *,
    timeout_seconds: int,
) -> bool:
    deadline = (
        time.monotonic()
        + timeout_seconds
    )

    while time.monotonic() < deadline:
        if service.health_url:
            if url_is_healthy(
                service.health_url
            ):
                return True
        elif service.port is not None:
            if port_is_open(
                service.port
            ):
                return True
        else:
            return True

        time.sleep(1)

    return False


def stop_pid(
    pid: int,
) -> bool:
    if not pid_is_running(pid):
        return True

    result = subprocess.run(
        [
            "taskkill",
            "/PID",
            str(pid),
            "/T",
            "/F",
        ],
        check=False,
        capture_output=True,
        text=True,
        creationflags=CREATE_NO_WINDOW,
    )

    return result.returncode == 0


def stop_managed_services() -> int:
    state = load_state()

    if not state:
        print(
            "No launcher-managed services "
            "were found."
        )
        return 0

    failures = 0

    for service in reversed(SERVICES):
        item = state.get(
            service.key,
            {},
        )
        pid = item.get("pid")

        if not isinstance(pid, int):
            print(
                f"[SKIP] {service.display_name}: "
                "no managed PID."
            )
            continue

        print(
            f"[STOP] {service.display_name} "
            f"(PID {pid})"
        )

        if stop_pid(pid):
            print(
                f"[OK]   {service.display_name} "
                "stopped."
            )
        else:
            failures += 1
            print(
                f"[FAIL] {service.display_name} "
                "could not be stopped."
            )

    if failures == 0:
        STATE_PATH.unlink(
            missing_ok=True
        )

    return 1 if failures else 0


def print_status() -> int:
    ensure_layout()
    state = load_state()

    print(
        "=" * 58
    )
    print(
        "KAIRO PLATFORM STATUS"
    )
    print(
        "=" * 58
    )

    all_running = True

    for service in SERVICES:
        running = service_is_running(
            service,
            state,
        )

        all_running = (
            all_running and running
        )

        health = "RUNNING" if running else "STOPPED"

        if (
            running
            and service.health_url
        ):
            health = (
                "HEALTHY"
                if url_is_healthy(
                    service.health_url
                )
                else "STARTING"
            )

        print(
            f"{service.display_name:<18}"
            f"{health}"
        )

    print(
        "=" * 58
    )

    return 0 if all_running else 1


def start_platform(
    *,
    foreground: bool,
    no_browser: bool,
    timeout_seconds: int,
) -> int:
    ensure_layout()
    state = load_state()
    changed = False
    started_services: list[
        ServiceDefinition
    ] = []

    print(
        "=" * 58
    )
    print(
        "KAIRO SMART LAUNCHER"
    )
    print(
        "=" * 58
    )

    for service in SERVICES:
        if service_is_running(
            service,
            state,
        ):
            print(
                f"[OK]    {service.display_name} "
                "already running."
            )
            continue

        print(
            f"[START] {service.display_name}"
        )

        try:
            process = start_service(
                service,
                foreground=foreground,
            )
        except OSError as error:
            print(
                f"[FAIL]  {service.display_name}: "
                f"{error}"
            )
            continue

        state[service.key] = {
            "pid": process.pid,
            "started_at": time.time(),
            "foreground": foreground,
            "command": list(
                service.command
            ),
        }
        save_state(state)
        changed = True
        started_services.append(service)

        if (
            service.health_url is not None
            or service.port is not None
        ):
            print(
                f"[WAIT]  Waiting for "
                f"{service.display_name}..."
            )

            if wait_for_service(
                service,
                timeout_seconds=(
                    timeout_seconds
                ),
            ):
                print(
                    f"[READY] {service.display_name}"
                )
            else:
                print(
                    f"[WARN]  {service.display_name} "
                    "did not become ready within "
                    f"{timeout_seconds} seconds."
                )
        else:
            time.sleep(1)

    print(
        "=" * 58
    )

    if changed:
        print(
            "Missing KAIRO services were started."
        )
    else:
        print(
            "All KAIRO services were already "
            "running. Nothing to start."
        )

    frontend_ready = url_is_healthy(
        FRONTEND_URL
    )

    if frontend_ready:
        print(
            f"Dashboard: {FRONTEND_URL}"
        )

        if not no_browser:
            webbrowser.open(
                FRONTEND_URL,
                new=2,
            )
            print(
                "Dashboard opened in the browser."
            )
    else:
        print(
            "Frontend is not ready, so the "
            "browser was not opened."
        )

    print(
        "=" * 58
    )

    return 0


def main() -> int:
    arguments = parse_args()

    try:
        if arguments.stop:
            return stop_managed_services()

        if arguments.restart:
            stop_result = (
                stop_managed_services()
            )

            if stop_result != 0:
                return stop_result

            time.sleep(2)

            return start_platform(
                foreground=(
                    arguments.foreground
                ),
                no_browser=(
                    arguments.no_browser
                ),
                timeout_seconds=(
                    arguments.timeout
                ),
            )

        if arguments.status:
            return print_status()

        return start_platform(
            foreground=arguments.foreground,
            no_browser=arguments.no_browser,
            timeout_seconds=arguments.timeout,
        )
    except RuntimeError as error:
        print(
            f"KAIRO launcher error: {error}"
        )
        return 1
    except KeyboardInterrupt:
        print(
            "\nLauncher interrupted."
        )
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
