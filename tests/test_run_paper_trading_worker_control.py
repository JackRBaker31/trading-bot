from app.run_paper_trading_worker import (
    parse_args,
)


def test_parses_worker_control_paths() -> None:
    args = parse_args(
        [
            "--config",
            "paper.json",
            "--database",
            "data/test.db",
            "--lock-file",
            "data/test.lock",
            "--stop-file",
            "data/test.stop",
            "--pid-file",
            "data/test.pid",
        ]
    )

    assert args.config == "paper.json"
    assert args.database == "data/test.db"
    assert args.lock_file == "data/test.lock"
    assert args.stop_file == "data/test.stop"
    assert args.pid_file == "data/test.pid"
