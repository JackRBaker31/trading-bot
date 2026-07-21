from app.run_paper_trading_worker import (
    parse_args,
)


def test_parses_paper_worker_arguments() -> None:
    args = parse_args(
        [
            "--config",
            "paper.json",
            "--database",
            "data/test.db",
            "--lock-file",
            "data/test.lock",
        ]
    )

    assert args.config == "paper.json"
    assert args.database == "data/test.db"
    assert args.lock_file == "data/test.lock"
