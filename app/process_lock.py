import os
from pathlib import Path

from app.application_errors import TradingOperationError


class ProcessLock:
    def __init__(self, *, path: str) -> None:
        cleaned_path = path.strip()
        if not cleaned_path:
            raise ValueError("Process-lock path is required.")
        self._path = Path(cleaned_path)
        self._acquired = False

    def acquire(self) -> None:
        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        try:
            descriptor = os.open(
                self._path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            )
        except FileExistsError as error:
            raise TradingOperationError(
                "Another paper-trading worker is already active.",
                code="PAPER_WORKER_ALREADY_RUNNING",
                context={"lock_path": str(self._path)},
            ) from error

        with os.fdopen(descriptor, "w") as file:
            file.write(str(os.getpid()))
        self._acquired = True

    def release(self) -> None:
        if not self._acquired:
            return
        self._path.unlink(missing_ok=True)
        self._acquired = False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        del exc_type, exc_value, traceback
        self.release()
