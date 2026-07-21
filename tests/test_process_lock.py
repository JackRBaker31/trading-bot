import pytest

from app.application_errors import (
    TradingOperationError,
)
from app.process_lock import ProcessLock


def test_process_lock_is_created_and_removed(
    tmp_path,
) -> None:
    path = tmp_path / "worker.lock"

    with ProcessLock(path=str(path)):
        assert path.exists()
        assert path.read_text().strip()

    assert not path.exists()


def test_second_process_lock_is_rejected(
    tmp_path,
) -> None:
    path = tmp_path / "worker.lock"
    first = ProcessLock(path=str(path))
    first.acquire()

    try:
        with pytest.raises(
            TradingOperationError,
            match="already active",
        ):
            ProcessLock(
                path=str(path)
            ).acquire()
    finally:
        first.release()
