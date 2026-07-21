import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from app.application_errors import (
    TradingOperationError,
)
from app.paper_trading_process import (
    PaperTradingProcessState,
    PaperTradingProcessStatus,
)


class SpawnedProcessLike(Protocol):
    pid: int


PopenFactory = Callable[..., SpawnedProcessLike]
ProcessAliveProvider = Callable[[int], bool]


def _default_process_alive(
    process_id: int,
) -> bool:
    if process_id <= 0:
        return False

    try:
        os.kill(process_id, 0)
    except OSError:
        return False

    return True


class PaperTradingProcessController:
    def __init__(
        self,
        *,
        config_path: str = "config.json",
        database_path: str = "data/application.db",
        lock_path: str = "data/paper_trading.lock",
        stop_path: str = "data/paper_trading.stop",
        pid_path: str = "data/paper_trading.pid",
        log_path: str = (
            "data/paper_trading_worker.log"
        ),
        working_directory: str = ".",
        python_executable: str | None = None,
        popen_factory: PopenFactory | None = None,
        process_alive_provider: (
            ProcessAliveProvider | None
        ) = None,
    ) -> None:
        self._config_path = self._required_path(
            config_path,
            "Configuration path",
        )
        self._database_path = self._required_path(
            database_path,
            "Database path",
        )
        self._lock_path = self._required_path(
            lock_path,
            "Lock path",
        )
        self._stop_path = self._required_path(
            stop_path,
            "Stop path",
        )
        self._pid_path = self._required_path(
            pid_path,
            "PID path",
        )
        self._log_path = self._required_path(
            log_path,
            "Worker-log path",
        )
        self._working_directory = (
            Path(working_directory)
        )
        self._python_executable = (
            python_executable
            or sys.executable
        )
        self._popen_factory = (
            popen_factory
            or subprocess.Popen
        )
        self._process_alive = (
            process_alive_provider
            or _default_process_alive
        )

    def get_status(
        self,
    ) -> PaperTradingProcessStatus:
        process_id = self._read_process_id()
        lock_present = self._lock_path.exists()
        stop_requested = self._stop_path.exists()

        if process_id is None:
            if lock_present or stop_requested:
                self._cleanup_state()
                return PaperTradingProcessStatus(
                    state=(
                        PaperTradingProcessState
                        .STOPPED
                    ),
                    process_id=None,
                    lock_present=False,
                    stop_requested=False,
                    stale_state_cleaned=True,
                )

            return PaperTradingProcessStatus(
                state=(
                    PaperTradingProcessState.STOPPED
                ),
                process_id=None,
                lock_present=False,
                stop_requested=False,
            )

        if not self._process_alive(process_id):
            self._cleanup_state()
            return PaperTradingProcessStatus(
                state=(
                    PaperTradingProcessState.STOPPED
                ),
                process_id=None,
                lock_present=False,
                stop_requested=False,
                stale_state_cleaned=True,
            )

        if stop_requested:
            state = (
                PaperTradingProcessState
                .STOP_REQUESTED
            )
        elif lock_present:
            state = (
                PaperTradingProcessState.RUNNING
            )
        else:
            state = (
                PaperTradingProcessState.STARTING
            )

        return PaperTradingProcessStatus(
            state=state,
            process_id=process_id,
            lock_present=lock_present,
            stop_requested=stop_requested,
        )

    def start(
        self,
    ) -> PaperTradingProcessStatus:
        current = self.get_status()

        if current.active:
            raise TradingOperationError(
                "The paper-trading worker is "
                "already active.",
                code="PAPER_WORKER_ALREADY_RUNNING",
                context={
                    "process_id": current.process_id,
                    "state": current.state.value,
                },
            )

        self._prepare_paths()
        self._stop_path.unlink(
            missing_ok=True
        )
        self._pid_path.unlink(
            missing_ok=True
        )
        self._lock_path.unlink(
            missing_ok=True
        )

        command = [
            self._python_executable,
            "-m",
            "app.run_paper_trading_worker",
            "--config",
            str(self._config_path),
            "--database",
            str(self._database_path),
            "--lock-file",
            str(self._lock_path),
            "--stop-file",
            str(self._stop_path),
            "--pid-file",
            str(self._pid_path),
        ]

        creation_flags = 0
        start_new_session = False

        if os.name == "nt":
            creation_flags = (
                getattr(
                    subprocess,
                    "CREATE_NEW_PROCESS_GROUP",
                    0,
                )
                | getattr(
                    subprocess,
                    "CREATE_NO_WINDOW",
                    0,
                )
            )
        else:
            start_new_session = True

        try:
            with self._log_path.open(
                mode="a",
                encoding="utf-8",
            ) as log_file:
                process = self._popen_factory(
                    command,
                    cwd=str(
                        self._working_directory
                    ),
                    stdin=subprocess.DEVNULL,
                    stdout=log_file,
                    stderr=log_file,
                    close_fds=True,
                    creationflags=creation_flags,
                    start_new_session=(
                        start_new_session
                    ),
                )
        except (
            OSError,
            subprocess.SubprocessError,
        ) as error:
            raise TradingOperationError(
                "The paper-trading worker could "
                "not be started.",
                code="PAPER_WORKER_START_FAILED",
                context={
                    "working_directory": str(
                        self._working_directory
                    )
                },
            ) from error

        self._pid_path.write_text(
            str(process.pid),
            encoding="utf-8",
        )

        return PaperTradingProcessStatus(
            state=(
                PaperTradingProcessState.STARTING
            ),
            process_id=process.pid,
            lock_present=False,
            stop_requested=False,
        )

    def stop(
        self,
    ) -> PaperTradingProcessStatus:
        current = self.get_status()

        if not current.active:
            return current

        self._stop_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._stop_path.write_text(
            "stop\n",
            encoding="utf-8",
        )

        return PaperTradingProcessStatus(
            state=(
                PaperTradingProcessState
                .STOP_REQUESTED
            ),
            process_id=current.process_id,
            lock_present=current.lock_present,
            stop_requested=True,
        )

    def _read_process_id(
        self,
    ) -> int | None:
        for path in (
            self._pid_path,
            self._lock_path,
        ):
            if not path.exists():
                continue

            try:
                process_id = int(
                    path.read_text(
                        encoding="utf-8"
                    ).strip()
                )
            except (
                OSError,
                ValueError,
            ):
                continue

            if process_id > 0:
                return process_id

        return None

    def _cleanup_state(
        self,
    ) -> None:
        self._pid_path.unlink(
            missing_ok=True
        )
        self._lock_path.unlink(
            missing_ok=True
        )
        self._stop_path.unlink(
            missing_ok=True
        )

    def _prepare_paths(
        self,
    ) -> None:
        for path in (
            self._database_path,
            self._lock_path,
            self._stop_path,
            self._pid_path,
            self._log_path,
        ):
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

    @staticmethod
    def _required_path(
        value: str,
        name: str,
    ) -> Path:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                f"{name} is required."
            )

        return Path(cleaned)
