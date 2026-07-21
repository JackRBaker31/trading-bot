from app.run_run_history import (
    parse_args,
)


def test_parses_run_history_arguments() -> None:
    args = parse_args(
        [
            "--database",
            "data/test.db",
            "--limit",
            "5",
            "--type",
            "STRATEGY_REPORT",
        ]
    )

    assert args.database == "data/test.db"
    assert args.limit == 5
    assert args.type == "STRATEGY_REPORT"