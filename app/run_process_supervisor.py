from __future__ import annotations

import argparse
import json
import signal
import sys
from pathlib import Path

from app.environment import load_environment
from app.process_supervisor import ProcessSupervisor, default_processes


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start and supervise the KAIRO backend processes."
    )
    parser.add_argument("--working-directory", default=".")
    parser.add_argument("--status-file", default="data/supervisor_status.json")
    parser.add_argument("--pid-file", default="data/kairo_supervisor.pid")
    parser.add_argument("--log-directory", default="data/supervisor")
    parser.add_argument("--check-seconds", type=float, default=2.0)
    parser.add_argument("--max-restarts", type=int, default=5)
    parser.add_argument("--no-restart", action="store_true")
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print the last supervisor status and exit.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_environment()
    args = parse_args(argv)

    if args.status:
        path = Path(args.status_file)
        if not path.exists():
            print("No supervisor status has been recorded.")
            return 1
        payload = json.loads(path.read_text(encoding="utf-8"))
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    supervisor = ProcessSupervisor(
        processes=default_processes(
            python_executable=sys.executable,
            log_directory=args.log_directory,
        ),
        working_directory=args.working_directory,
        status_path=args.status_file,
        pid_path=args.pid_file,
        check_seconds=args.check_seconds,
        restart_enabled=not args.no_restart,
        max_restarts=args.max_restarts,
    )

    def request_stop(signum, frame) -> None:
        del signum, frame
        supervisor.request_stop()

    signal.signal(signal.SIGINT, request_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, request_stop)

    print("KAIRO PROCESS SUPERVISOR STARTED")
    print("Managing: API, Job Worker, Scheduler")
    print("Paper trading remains controlled by the existing API.")
    try:
        supervisor.run_forever()
    except RuntimeError as error:
        print(f"ERROR: {error}")
        return 1
    finally:
        print("KAIRO PROCESS SUPERVISOR STOPPED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())