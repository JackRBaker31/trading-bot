from app.paper_trading_process import (
    PaperTradingProcessState,
    PaperTradingProcessStatus,
)


def test_process_status_dictionary() -> None:
    status = PaperTradingProcessStatus(
        state=(
            PaperTradingProcessState.RUNNING
        ),
        process_id=123,
        lock_present=True,
        stop_requested=False,
    )

    assert status.active is True
    assert status.to_dictionary() == {
        "state": "RUNNING",
        "active": True,
        "process_id": 123,
        "lock_present": True,
        "stop_requested": False,
        "stale_state_cleaned": False,
    }
