import argparse
import os
import signal
import threading
from pathlib import Path

from app.environment import load_environment
from app.logging_config import setup_logging
from app.process_lock import ProcessLock
from app.run_history_repository import (
    RunHistoryRepository,
)
from app.run_history_service import (
    RunHistoryService,
)
from app.trading_application import (
    TradingApplicationRequest,
)
from app.trading_application_service import (
    TradingApplicationService,
)


def parse_args(
    argv: list[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the automatic Trading 212 DEMO "
            "paper-trading worker."
        )
    )
    parser.add_argument(
        "--config",
        default="config.json",
    )
    parser.add_argument(
        "--database",
        default="data/application.db",
    )
    parser.add_argument(
        "--lock-file",
        default="data/paper_trading.lock",
    )
    parser.add_argument(
        "--stop-file",
        default="data/paper_trading.stop",
    )
    parser.add_argument(
        "--pid-file",
        default="data/paper_trading.pid",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    setup_logging()
    load_environment()

    stop_event = threading.Event()
    stop_path = Path(args.stop_file)
    pid_path = Path(args.pid_file)

    def request_stop(
        signum,
        frame,
    ) -> None:
        del signum, frame
        stop_event.set()

    signal.signal(
        signal.SIGINT,
        request_stop,
    )
    signal.signal(
        signal.SIGTERM,
        request_stop,
    )

    stop_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    pid_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    stop_path.unlink(
        missing_ok=True
    )
    pid_path.write_text(
        str(os.getpid()),
        encoding="utf-8",
    )

    history_service = RunHistoryService(
        repository=RunHistoryRepository(
            database_path=args.database
        )
    )
    history_service.initialize()

    service = TradingApplicationService(
        run_history_service=history_service
    )

    try:
        with ProcessLock(
            path=args.lock_file
        ):
            service.run(
                request=(
                    TradingApplicationRequest(
                        config_path=args.config,
                        require_paper_mode=True,
                    )
                ),
                stop_requested=(
                    lambda: (
                        stop_event.is_set()
                        or stop_path.exists()
                    )
                ),
            )
    finally:
        pid_path.unlink(
            missing_ok=True
        )
        stop_path.unlink(
            missing_ok=True
        )


if __name__ == "__main__":
    main()
