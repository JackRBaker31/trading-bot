import pytest

from app.application_errors import (
    TradingOperationError,
)
from app.paper_trading_process import (
    PaperTradingProcessState,
)
from app.paper_trading_process_controller import (
    PaperTradingProcessController,
)


class FakeProcess:
    pid = 4321


def create_controller(
    tmp_path,
    *,
    alive: bool = True,
):
    calls = []

    def fake_popen(
        command,
        **kwargs,
    ):
        calls.append(
            (command, kwargs)
        )
        return FakeProcess()

    controller = PaperTradingProcessController(
        config_path=str(
            tmp_path / "config.json"
        ),
        database_path=str(
            tmp_path / "application.db"
        ),
        lock_path=str(
            tmp_path / "worker.lock"
        ),
        stop_path=str(
            tmp_path / "worker.stop"
        ),
        pid_path=str(
            tmp_path / "worker.pid"
        ),
        log_path=str(
            tmp_path / "worker.log"
        ),
        working_directory=str(tmp_path),
        python_executable="python",
        popen_factory=fake_popen,
        process_alive_provider=(
            lambda process_id: (
                alive
                and process_id == 4321
            )
        ),
    )
    return controller, calls


def test_starts_worker_process(
    tmp_path,
) -> None:
    controller, calls = create_controller(
        tmp_path
    )

    status = controller.start()

    assert status.state == (
        PaperTradingProcessState.STARTING
    )
    assert status.process_id == 4321
    assert len(calls) == 1
    assert (
        "app.run_paper_trading_worker"
        in calls[0][0]
    )


def test_reports_running_when_lock_exists(
    tmp_path,
) -> None:
    controller, _ = create_controller(
        tmp_path
    )
    controller.start()
    (tmp_path / "worker.lock").write_text(
        "4321",
        encoding="utf-8",
    )

    status = controller.get_status()

    assert status.state == (
        PaperTradingProcessState.RUNNING
    )
    assert status.lock_present is True


def test_stop_creates_graceful_stop_request(
    tmp_path,
) -> None:
    controller, _ = create_controller(
        tmp_path
    )
    controller.start()
    (tmp_path / "worker.lock").write_text(
        "4321",
        encoding="utf-8",
    )

    status = controller.stop()

    assert status.state == (
        PaperTradingProcessState
        .STOP_REQUESTED
    )
    assert (
        tmp_path / "worker.stop"
    ).exists()


def test_rejects_second_active_worker(
    tmp_path,
) -> None:
    controller, _ = create_controller(
        tmp_path
    )
    controller.start()

    with pytest.raises(
        TradingOperationError,
    ) as captured:
        controller.start()

    assert captured.value.code == (
        "PAPER_WORKER_ALREADY_RUNNING"
    )


def test_cleans_stale_process_files(
    tmp_path,
) -> None:
    controller, _ = create_controller(
        tmp_path,
        alive=False,
    )
    (tmp_path / "worker.pid").write_text(
        "4321",
        encoding="utf-8",
    )
    (tmp_path / "worker.lock").write_text(
        "4321",
        encoding="utf-8",
    )

    status = controller.get_status()

    assert status.state == (
        PaperTradingProcessState.STOPPED
    )
    assert status.stale_state_cleaned is True
    assert not (
        tmp_path / "worker.pid"
    ).exists()
    assert not (
        tmp_path / "worker.lock"
    ).exists()
