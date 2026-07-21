from app.run_job_worker import parse_args


def test_parses_one_shot_worker_arguments() -> None:
    args = parse_args(
        [
            "--database",
            "data/test.db",
            "--once",
            "--poll-seconds",
            "1.5",
        ]
    )

    assert args.database == "data/test.db"
    assert args.once is True
    assert args.poll_seconds == 1.5
