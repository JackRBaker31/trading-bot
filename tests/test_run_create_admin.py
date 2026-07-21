from app.run_create_admin import parse_args


def test_parses_admin_creation_arguments() -> None:
    args = parse_args(
        [
            "--username",
            "admin",
            "--database",
            "data/test.db",
        ]
    )

    assert args.username == "admin"
    assert args.database == "data/test.db"
