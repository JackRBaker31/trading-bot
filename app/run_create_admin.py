import argparse
from getpass import getpass

from app.auth_repository import (
    AuthenticationRepository,
)
from app.auth_service import (
    AuthenticationService,
)
from app.environment import load_environment


def parse_args(
    argv: list[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create an administrator account."
        )
    )
    parser.add_argument(
        "--username",
        required=True,
    )
    parser.add_argument(
        "--database",
        default="data/application.db",
    )
    return parser.parse_args(argv)


def main() -> None:
    load_environment()
    args = parse_args()

    password = getpass(
        "Administrator password: "
    )
    confirmation = getpass(
        "Confirm password: "
    )

    if password != confirmation:
        raise ValueError(
            "Passwords do not match."
        )

    service = AuthenticationService(
        repository=AuthenticationRepository(
            database_path=args.database
        )
    )
    service.initialize()

    user = service.create_user(
        username=args.username,
        password=password,
        role="ADMIN",
    )

    print(
        f"Created administrator: "
        f"{user.username}"
    )


if __name__ == "__main__":
    main()
